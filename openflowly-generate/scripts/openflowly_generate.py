#!/usr/bin/env python3
"""Batch image/video generation client for the Openflowly API."""
import argparse, json, mimetypes, os, stat, sys, time, ssl, uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

DEFAULT_BASE = "https://www.openflowly.com/v1"
DEFAULT_UPLOAD_BASE = "https://www.openflowly.com/v1"
QUALITY_CHOICES = ("low", "medium", "high")
DEFAULT_IMAGE_QUALITY = "low"
TRANSPARENT_BACKGROUND_MODEL = "gpt image 2.5"
DEFAULTS = {"image": {"model": "Gpt Image 2.5", "resolution": "1K", "quality": DEFAULT_IMAGE_QUALITY},
            "video": {"model": "Seedance 2 Mini", "resolution": "480p"}}

def normalize_quality(value):
    normalized = str(value).strip().lower()
    if normalized not in QUALITY_CHOICES:
        raise argparse.ArgumentTypeError(
            f"invalid quality '{value}'; choose from {', '.join(QUALITY_CHOICES)}"
        )
    return normalized

def config_path(): return Path.home() / ".openflowly" / "config.json"
def model_config_path(): return Path.home() / ".openflowly" / "model_config.json"

def write_private_json(path, value):
    path.parent.mkdir(mode=0o700, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
    os.replace(temporary, path)

def load_key():
    key = os.getenv("OPENFLOWLY_API_KEY")
    if key: return key.strip()
    try: return str(json.loads(config_path().read_text()).get("api_key", "")).strip()
    except (OSError, ValueError, TypeError): return ""

def request_json(url, key, method="GET", body=None, headers=None):
    h = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    if body is not None: h["Content-Type"] = "application/json"
    if headers: h.update(headers)
    req = Request(url, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)
    try:
        with urlopen(req, timeout=300, context=SSL_CONTEXT) as response: return json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except URLError as exc: raise RuntimeError(f"Network error: {exc.reason}") from exc

def refresh_model_config(base_url, key):
    normalized_base = base_url.rstrip("/")
    result = request_json(f"{normalized_base}/config?all=false", key or "", headers={})
    if not isinstance(result, dict) or not isinstance(result.get("providers"), list):
        raise RuntimeError("Model config response did not contain providers")
    write_private_json(model_config_path(), {
        "base_url": normalized_base,
        "fetched_at": int(time.time()),
        "config": result,
    })
    return result

def load_model_config(base_url, key, refresh=False):
    normalized_base = base_url.rstrip("/")
    if not refresh:
        try:
            cached = json.loads(model_config_path().read_text())
            if cached.get("base_url") == normalized_base and isinstance(cached.get("config", {}).get("providers"), list):
                return cached["config"]
        except (OSError, ValueError, TypeError, AttributeError):
            pass
    return refresh_model_config(normalized_base, key)

def upload_file(path, base_url, key):
    file_path = Path(path).expanduser()
    if not file_path.is_file(): raise RuntimeError(f"Reference image not found: {path}")
    content = file_path.read_bytes()
    filename = file_path.name.replace("/", "_")
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    boundary = "----OpenflowlyGenerateBoundary7d9f"
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"source\"\r\n\r\nai\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode() + content + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    req = Request(f"{base_url.rstrip('/')}/upload/", data=b"".join(parts), headers={
        "Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json"
    }, method="POST")
    try:
        with urlopen(req, timeout=300, context=SSL_CONTEXT) as response:
            result = json.loads(response.read().decode())
    except HTTPError as exc:
        raise RuntimeError(f"Upload HTTP {exc.code}: {exc.read().decode(errors='replace')[:1000]}") from exc
    except URLError as exc: raise RuntimeError(f"Upload network error: {exc.reason}") from exc
    url = result.get("url")
    if not url: raise RuntimeError("Upload response did not contain a URL")
    return url

def first_value(obj, names):
    if isinstance(obj, dict):
        for name in names:
            if obj.get(name): return obj[name]
        for value in obj.values():
            found = first_value(value, names)
            if found: return found
    elif isinstance(obj, list):
        for value in obj:
            found = first_value(value, names)
            if found: return found
    return None

def media_url(obj):
    value = first_value(obj, ("url", "image_url", "video_url"))
    if isinstance(value, list): return value[0] if value else None
    return value if isinstance(value, str) and value.startswith(("http://", "https://", "data:")) else None

def download_media(url, output_dir, index, task_id):
    if not url or url.startswith("data:"):
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".mp3", ".wav"}:
        suffix = ".bin"
    safe_task = "".join(ch if ch.isalnum() else "_" for ch in (task_id or "direct"))
    path = output_dir / f"scene-{index:02d}-{safe_task}{suffix}"
    request = Request(url, headers={"User-Agent": "openflowly-generate/1.0"})
    with urlopen(request, timeout=300, context=SSL_CONTEXT) as response:
        data = response.read()
    if not data:
        raise RuntimeError(f"Downloaded media is empty: {url}")
    path.write_bytes(data)
    return str(path.resolve())

def task_status(obj): return str(first_value(obj, ("status", "state")) or "").lower()

def find_model_config(kind, model_name, config):
    target = str(model_name).strip().casefold()
    for provider in config.get("providers", []):
        for model in provider.get("models", []):
            identifiers = (model.get("model_name"), model.get("model"), model.get("id"))
            if model.get("category") == kind and target in {str(value).strip().casefold() for value in identifiers if value}:
                return model
    raise RuntimeError(f"Enabled {kind} model not found in cached model config: {model_name}. Run refresh-config to update it.")

def route_reference_fields(kind, model_config, subject_images=None, subject_videos=None,
                           subject_audios=None, first_frame=None, end_frame=None):
    subject_images = list(subject_images or [])
    subject_videos = list(subject_videos or [])
    subject_audios = list(subject_audios or [])
    has_subject = bool(subject_images or subject_videos or subject_audios)
    has_frames = bool(first_frame or end_frame)

    if kind == "image":
        if has_frames: raise ValueError("Image models do not accept first/end-frame parameters")
        if subject_videos or subject_audios: raise ValueError("Image models only accept image subject references")
        if has_subject and str(model_config.get("subject_reference_field_config", "0")) == "0":
            raise ValueError("Selected image model does not support subject references")
        return {"image_urls": subject_images} if subject_images else {}

    first_last_config = str(model_config.get("first_last_frame_field_config", "0"))
    subject_config = str(model_config.get("subject_reference_field_config", "0"))
    if has_frames:
        if first_last_config == "0":
            raise ValueError("Selected video model does not support first/end frames")
        if first_last_config == "1":
            if subject_videos or subject_audios:
                raise ValueError("image_with_roles first/end-frame mode cannot be combined with video/audio subject references")
            if len(subject_images) > 1:
                raise ValueError("image_with_roles first/end-frame mode accepts at most one subject reference image")
            roles = []
            if first_frame: roles.append({"url": first_frame, "role": "first_frame"})
            if end_frame: roles.append({"url": end_frame, "role": "last_frame"})
            if subject_images: roles.append({"url": subject_images[0], "role": "reference"})
            return {"image_with_roles": roles}
        if has_subject:
            raise ValueError("This model's first/end-frame mode cannot be combined with subject references")
        if first_last_config == "2":
            if end_frame: raise ValueError("Selected video model supports a first frame only")
            return {"first_frame_image": first_frame} if first_frame else {}
        if first_last_config == "3":
            fields = {}
            if first_frame: fields["first_frame_image"] = first_frame
            if end_frame: fields["end_frame_image"] = end_frame
            return fields
        raise ValueError(f"Unknown first_last_frame_field_config: {first_last_config}")

    if not has_subject: return {}
    if subject_config == "0":
        raise ValueError("Selected video model does not support subject references")
    if subject_config == "1":
        if subject_videos or subject_audios:
            raise ValueError("Selected video model only accepts image subject references")
        return {"image_urls": subject_images}
    if subject_config == "2":
        fields = {}
        if subject_images: fields["image_urls"] = subject_images
        if subject_videos: fields["video_urls"] = subject_videos
        if subject_audios: fields["audio_urls"] = subject_audios
        return fields
    if subject_config == "3":
        if subject_audios:
            raise ValueError("Selected video model does not accept audio subject references")
        fields = {}
        if subject_images: fields["image_urls"] = subject_images
        if subject_videos: fields["video_list"] = subject_videos
        return fields
    raise ValueError(f"Unknown subject_reference_field_config: {subject_config}")

def prepare_reference_fields(kind, args, model_config):
    legacy_images = list(args.reference_image or [])
    legacy_urls = list(args.reference_url or [])
    if kind == "video" and (legacy_images or legacy_urls):
        raise ValueError("For video, replace ambiguous --reference-image/--reference-url with explicit subject or frame arguments")

    subject_paths = legacy_images + list(args.subject_reference_image or [])
    subject_urls = legacy_urls + list(args.subject_reference_url or [])
    subject_videos = list(args.subject_reference_video_url or [])
    subject_audios = list(args.subject_reference_audio_url or [])
    if args.first_frame_image and args.first_frame_url:
        raise ValueError("Provide only one of --first-frame-image or --first-frame-url")
    if args.end_frame_image and args.end_frame_url:
        raise ValueError("Provide only one of --end-frame-image/--last-frame-image or --end-frame-url/--last-frame-url")
    first_frame = args.first_frame_url or args.first_frame_image
    end_frame = args.end_frame_url or args.end_frame_image

    # Validate the model-specific combination before uploading local files.
    route_reference_fields(kind, model_config, subject_urls + subject_paths, subject_videos,
                           subject_audios, first_frame, end_frame)
    # Upload local media through the public Openflowly host so returned URLs are
    # reachable by the downstream generation service.
    subject_urls += [upload_file(path, DEFAULT_UPLOAD_BASE, args.api_key) for path in subject_paths]
    if args.first_frame_image: first_frame = upload_file(args.first_frame_image, DEFAULT_UPLOAD_BASE, args.api_key)
    if args.end_frame_image: end_frame = upload_file(args.end_frame_image, DEFAULT_UPLOAD_BASE, args.api_key)
    return route_reference_fields(kind, model_config, subject_urls, subject_videos,
                                  subject_audios, first_frame, end_frame)

def submit_generation(kind, args, prompt, index):
    options = DEFAULTS[kind].copy(); options.update({k: v for k, v in vars(args).items() if v is not None and k in ("model", "resolution", "quality", "size", "aspect_ratio", "duration")})
    model_config = getattr(args, "model_config", {})
    if getattr(args, "transparent_background", False) and kind != "image":
        raise ValueError("--transparent-background is only supported for image generation")
    if kind == "image":
        # Keep low as the enforced default; only an explicit CLI value overrides it.
        options["quality"] = args.quality if args.quality is not None else DEFAULT_IMAGE_QUALITY
    if kind == "image" and model_config.get("quality"):
        options["quality"] = normalize_quality(options["quality"])
    elif kind == "image":
        if args.quality is not None: raise ValueError("Selected image model does not support --quality")
        options.pop("quality", None)
    elif args.quality is not None: raise ValueError("--quality is only supported for image generation")
    body = {"model": options.pop("model"), "prompt": prompt, "n": args.count if kind == "image" else 1, **options}
    if getattr(args, "transparent_background", False):
        identifiers = {str(model_config.get(key, "")).strip().casefold() for key in ("model_name", "model", "id") if model_config.get(key)}
        if TRANSPARENT_BACKGROUND_MODEL not in identifiers:
            raise ValueError("Transparent background is only supported by Gpt Image 2.5")
        body["background"] = "transparent"
    body.update(getattr(args, "reference_fields", {}))
    if kind == "video" and body.get("duration") is None: body.pop("duration", None)
    endpoint = f"{args.base_url.rstrip('/')}/{'images' if kind == 'image' else 'videos'}/generations"
    result = request_json(endpoint, args.api_key, "POST", body)
    task_id = first_value(result, ("task_id", "taskId", "id"))
    direct = media_url(result)
    if direct:
        return {"index": index, "prompt": prompt, "model": body["model"], "task_id": task_id, "status": "succeeded", "url": direct}
    if not task_id:
        raise RuntimeError("Generation response did not contain a task ID or media URL")
    return {"index": index, "prompt": prompt, "model": body["model"], "task_id": task_id, "status": "submitted", "url": None}

def poll_generation(args, item):
    task_id = item.get("task_id")
    if not task_id:
        return item
    if item.get("status") == "succeeded" and item.get("url"):
        return item
    for attempt in range(1, 21):
        time.sleep(10)
        result = request_json(f"{args.base_url.rstrip('/')}/tasks/{task_id}", args.api_key, headers={"X-Model-Name": item["model"]})
        status = task_status(result)
        direct = media_url(result)
        if direct:
            item.update({"status": "succeeded", "url": direct})
            return item
        if status in {"completed", "succeeded", "success", "done", "finish", "finished"}:
            # A terminal status without a media URL is not downloadable yet;
            # keep polling instead of reporting a false success.
            continue
        if status in {"failed", "error", "fail", "cancelled", "canceled", "timeout"}:
            item.update({"status": status, "url": None})
            return item
    item.update({"status": "poll_timeout", "url": None})
    return item

def main():
    parser = argparse.ArgumentParser(description="Batch generate media with Openflowly")
    parser.add_argument("--base-url", default=os.getenv("OPENFLOWLY_BASE_URL", DEFAULT_BASE)); parser.add_argument("--api-key", default=load_key())
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("configure"); c.add_argument("--api-key", required=True); c.set_defaults(func=lambda a: configure(a.api_key, a.base_url))
    u = sub.add_parser("refresh-config", aliases=("update-models",), help="Fetch and cache the latest enabled model config"); u.set_defaults(func=run_refresh_config)
    m = sub.add_parser("models", help="List enabled models from the local cache"); m.add_argument("--refresh", action="store_true", help="Refresh the cache before listing"); m.set_defaults(func=list_models)
    g = sub.add_parser("generate"); g.add_argument("kind", choices=("image", "video")); g.add_argument("--prompt", action="append"); g.add_argument("--input-jsonl"); g.add_argument("--model"); g.add_argument("--resolution"); g.add_argument("--quality", type=normalize_quality, choices=QUALITY_CHOICES, help="Image quality (case-insensitive)"); g.add_argument("--size"); g.add_argument("--aspect-ratio", dest="aspect_ratio"); g.add_argument("--duration", type=int); g.add_argument("--count", type=int, default=1); g.add_argument("--output-dir", default=None, help="Fresh output directory for downloaded results")
    g.add_argument("--transparent-background", action="store_true", help="Generate an RGBA PNG with a transparent background (Gpt Image 2.5 images only)")
    g.add_argument("--reference-image", action="append", help="Legacy local subject image for image models; repeatable")
    g.add_argument("--reference-url", action="append", help="Legacy subject image URL for image models; repeatable")
    g.add_argument("--subject-reference-image", action="append", help="Local subject reference image; repeatable")
    g.add_argument("--subject-reference-url", action="append", help="Subject reference image URL; repeatable")
    g.add_argument("--subject-reference-video-url", action="append", help="Subject reference video URL; repeatable")
    g.add_argument("--subject-reference-audio-url", action="append", help="Subject reference audio URL; repeatable")
    g.add_argument("--first-frame-image", help="Local first-frame image for video generation")
    g.add_argument("--first-frame-url", help="First-frame image URL for video generation")
    g.add_argument("--end-frame-image", "--last-frame-image", dest="end_frame_image", help="Local end-frame image for video generation")
    g.add_argument("--end-frame-url", "--last-frame-url", dest="end_frame_url", help="End-frame image URL for video generation")
    g.set_defaults(func=run_generate)
    args = parser.parse_args(); args.func(args)

def configure(key, base_url=DEFAULT_BASE):
    write_private_json(config_path(), {"api_key": key.strip()})
    result = refresh_model_config(base_url, key.strip())
    model_count = sum(len(provider.get("models", [])) for provider in result.get("providers", []))
    print(f"Configured Openflowly API key at {config_path()}")
    print(f"Cached {model_count} models at {model_config_path()}")

def run_refresh_config(args):
    if not args.api_key: raise SystemExit("No API key. Run configure first.")
    result = refresh_model_config(args.base_url, args.api_key)
    model_count = sum(len(provider.get("models", [])) for provider in result.get("providers", []))
    print(f"Updated model config cache with {model_count} models at {model_config_path()}")

def list_models(args):
    result = load_model_config(args.base_url, args.api_key or "", refresh=args.refresh)
    rows = []
    for provider in result.get("providers", []):
        for model in provider.get("models", []):
            if model.get("status") in (None, "1", 1, True) and not model.get("hide_in_ui", False):
                rows.append({"provider": provider.get("name") or provider.get("id"), "category": model.get("category"), "model_name": model.get("model_name"), "model": model.get("model"), "resolution": model.get("resolution"), "size": model.get("size"), "quality": model.get("quality"), "subject_reference_field_config": model.get("subject_reference_field_config"), "first_last_frame_field_config": model.get("first_last_frame_field_config"), "max_image_size": model.get("max_image_size"), "max_image_count": model.get("max_image_count")})
    print(json.dumps(rows, ensure_ascii=False, indent=2))

def run_generate(args):
    if not args.api_key: raise SystemExit("No API key. Register at https://www.openflowly.com and provide your key, then run configure.")
    prompts = list(args.prompt or [])
    if args.input_jsonl:
        with open(args.input_jsonl, encoding="utf-8") as f:
            prompts += [json.loads(line)["prompt"] if line.lstrip().startswith("{") else line.strip() for line in f if line.strip()]
    if not prompts: raise SystemExit("Provide --prompt (repeatable) or --input-jsonl.")
    selected_model = args.model or DEFAULTS[args.kind]["model"]
    config = load_model_config(args.base_url, args.api_key)
    args.model_config = find_model_config(args.kind, selected_model, config)
    args.reference_fields = prepare_reference_fields(args.kind, args, args.model_config)
    args.output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else (Path.cwd() / "outputs" / f"openflowly-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}").resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    expanded = [p for p in prompts for _ in range(max(1, args.count))] if len(prompts) > 1 else prompts * max(1, args.count)
    results = []

    # Keep task state in memory only. This CLI submits and polls in one process;
    # it does not write tasks.jsonl or result records. Failed, timed-out, and
    # errored tasks therefore need no extra cleanup and leave no JSON residue.
    for i, prompt in enumerate(expanded, 1):
        item = {"index": i, "prompt": prompt, "model": selected_model, "status": "error", "url": None}
        try:
            item = submit_generation(args.kind, args, prompt, i)
            if item.get("status") != "error":
                item = poll_generation(args, item)
                item["local_output_path"] = download_media(item.get("url"), args.output_dir, i, item.get("task_id"))
        except Exception as exc:
            item.update({"status": "poll_error" if item.get("task_id") else "error", "url": None, "error": str(exc)})
        results.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)
    return results

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit(130)

---
name: openflowly-generate
description: Use the Openflowly API to batch-generate images or videos from one or more user prompts, including first-time API-key setup, default model selection, asynchronous task creation, and result polling. Trigger when the user asks to generate, batch-generate, render, or create AI images/videos through Openflowly.
---

# Openflowly Generate

Use this skill for Openflowly image/video generation requests. Keep the API key private and never print it back to the user.

## Empty input response

When the user invokes this skill without any generation request, return the following fixed introduction and do not call an API:

```text
Openflowly 图片/视频生成助手

我可以帮你批量生成图片或视频，也可以根据你提供的参考图片生成相似风格的内容。

你可以让我：

- 根据文字描述生成图片
- 根据文字描述生成视频
- 一次生成多张图片或多个视频
- 使用你上传的图片作为人物、产品、构图或风格参考
- 查询当前可用的生成模型
- 更新本地缓存的模型配置
- 按指定的画面比例生成，例如 16:9、9:16、1:1
- 为视频设置时长和清晰度

默认设置：

- 图片：高质量实拍与创意图片，默认使用 Gpt Image 2
- 视频：默认使用 Seedance 2 Mini，清晰度为 480p

开始生成时，你可以直接告诉我：

- 想生成图片还是视频
- 想生成什么内容，以及希望呈现的风格
- 需要生成几张或几个
- 图片比例，或视频时长
- 是否需要上传参考图片

例如：

“生成 3 张 16:9 的金毛犬花园实拍图，阳光自然、画面温暖。”

“参考我上传的图片，生成一个 9:16、8 秒的海边人物短视频。”
```

If the API key has not been configured, ask the user to register at `https://www.openflowly.com` and provide an API key only after they submit a concrete generation request.

## Configuration

On the first generation request, check whether `OPENFLOWLY_API_KEY` is set or the local config exists. If neither exists, tell the user: register at `https://www.openflowly.com`, create/copy an API key, and provide it in the chat. After the user provides it, configure it with:

```bash
python3 scripts/openflowly_generate.py configure --api-key '<KEY>'
```

The script stores the key in `~/.openflowly/config.json`, immediately fetches `GET /v1/config?all=false`, and stores that response in `~/.openflowly/model_config.json`. Both files use restrictive permissions. Prefer the environment variable when available. The default API base is `https://www.openflowly.com/v1`; override it with `OPENFLOWLY_BASE_URL` or `--base-url` only when the user explicitly provides another endpoint.

## Defaults

Unless the user selects another model, use:

- Images: `Gpt Image 2`, `resolution=1K`, `quality=low`.
- Videos: `Seedance 2 Mini`, `resolution=480p`.

Preserve user-specified model, resolution, quality, aspect ratio, duration, reference images, and count. For image generation, pass `--quality low`, `--quality medium`, or `--quality high`; the client accepts these values case-insensitively and always sends lowercase API values. Ask only for information that is required to construct the request, such as a missing prompt or an unavailable reference-image URL.

## Model config cache

Use the local model-config cache for generation and model listing. Do not call `/config` on every generation. If the cache is absent, invalid, or belongs to another base URL, fetch and save it once automatically for backward compatibility.

List cached models with:

```bash
python3 scripts/openflowly_generate.py models
```

Refresh the model configuration only when the user asks to update it, when a required model is missing, or when Openflowly model settings have changed:

```bash
python3 scripts/openflowly_generate.py refresh-config
# Alias:
python3 scripts/openflowly_generate.py update-models
```

Use `python3 scripts/openflowly_generate.py models --refresh` to refresh and list in one command. Refreshing calls `GET /v1/config?all=false` and atomically replaces the local cache. Never use `all=true`, because that administrative response may contain provider credentials.

## Model-specific reference fields

Read and inspect the selected model's cached `subject_reference_field_config` and `first_last_frame_field_config` before submitting any subject reference or first/end frame. Never infer the request field from the model name and never send every reference as `image_urls`.

Route subject references as follows:

| Config | Supported request fields |
| --- | --- |
| `0` | No subject reference; reject reference input. |
| `1` | Image subjects only: `image_urls`. |
| `2` | Separate media fields: `image_urls`, `video_urls`, and `audio_urls`. |
| `3` | Images in `image_urls`, videos in `video_list`; reject audio subjects. |

Route video first/end frames as follows:

| Config | Supported request fields |
| --- | --- |
| `0` | No first/end frames; reject frame input. |
| `1` | `image_with_roles`, using roles `first_frame`, `last_frame`, and optional `reference`. |
| `2` | `first_frame_image` only; reject an end frame. |
| `3` | `first_frame_image` and optional `end_frame_image`. |

Use explicit CLI arguments for video references: `--subject-reference-image`, `--subject-reference-url`, `--subject-reference-video-url`, `--subject-reference-audio-url`, `--first-frame-image`/`--first-frame-url`, and `--end-frame-image`/`--end-frame-url`. Treat `--last-frame-image` and `--last-frame-url` as aliases for the end-frame arguments. Reject ambiguous legacy `--reference-image` and `--reference-url` arguments for video generation; retain them only for image-model subject references.

When first/end-frame mode is active, follow the selected first/end-frame config instead of also emitting generic subject fields. For config `1`, allow at most one image subject and place it in `image_with_roles` with role `reference`. For configs `2` and `3`, reject simultaneous subject references because the Openflowly request builder treats the modes as exclusive. Validate the combination before uploading local files.

## Generation workflow

1. Normalize the request into `image` or `video`, one or more prompts, count, model, provider-supported options, and any reference media. Load the local model-config cache, resolve the selected model by `model_name`, provider model ID, or model ID, and route references according to the two model configuration fields above. The script uploads local reference files through `/v1/upload/` only after validation.
2. Run `scripts/openflowly_generate.py generate ...`. Use repeated `--prompt` for a small batch or `--input-jsonl` for a larger batch. The script submits each item to `/v1/images/generations` or `/v1/videos/generations`.
3. Extract the asynchronous task ID from common OpenAI/provider response shapes. If the response already contains a media URL, return it without polling. Request `include_media_data=true` whenever the caller needs an embeddable result.
4. For each task, wait 10 seconds between checks and poll `/v1/tasks/{task_id}?include_media_data=true` at most 20 times. Include `X-Model-Name` on every poll. Treat `completed`, `succeeded`, `success`, `done`, `finish`, and `finished` as success; treat `failed`, `error`, `fail`, `cancelled`, `canceled`, and `timeout` as failure.
5. Return a concise batch table with prompt, model, task ID, status, media URL, and, when requested, `media_data_url`. If the task is still pending after 20 polls, report timeout and retain the task ID for manual follow-up.

Do not claim that a task succeeded without a final media URL or an explicit successful status. Never expose authorization headers, saved config contents, or secrets in logs/output.

## Command examples

```bash
python3 scripts/openflowly_generate.py generate image \
  --prompt 'A cinematic product photo of a silver teapot on black stone' \
  --quality low \
  --count 3

python3 scripts/openflowly_generate.py generate video \
  --prompt 'A slow camera move through a neon-lit rainy alley' \
  --first-frame-image ./opening.png \
  --duration 8

python3 scripts/openflowly_generate.py generate image --input-jsonl prompts.jsonl

python3 scripts/openflowly_generate.py generate image \
  --prompt '保持人物姿态和构图，换成海边渔港的胶片实拍风格' \
  --reference-image ./reference.png --size '9:16'
```

See [API_REFERENCE.md](references/API_REFERENCE.md) for request fields and response-shape details.

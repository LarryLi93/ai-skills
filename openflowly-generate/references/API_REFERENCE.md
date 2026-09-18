# Openflowly API Reference

Base URL: `https://www.openflowly.com/v1`

Authentication: `Authorization: Bearer <OPENFLOWLY_API_KEY>`.

Reference upload: `POST /upload/` as `multipart/form-data` with `file` and `source=ai`; place the returned `url` in the model-configured subject-reference or first/end-frame field.

Latest model list: `GET /config?all=false`, returning enabled models under `providers[].models[]`. Fetch it during API-key configuration and cache it in `~/.openflowly/model_config.json`; generation reads that cache instead of calling the endpoint repeatedly. Refresh it explicitly with `refresh-config`, `update-models`, or `models --refresh`. Use `model_name` for Openflowly generation requests. Read `subject_reference_field_config` and `first_last_frame_field_config` before constructing any reference-media fields. Do not request `all=true` from this skill.

Generation endpoints:

- `POST /images/generations`: `model`, `prompt`, `n`, optional `resolution`, `quality`, `size`, `aspect_ratio`, `image_urls`. Send `quality` as lowercase `low`, `medium`, or `high`. For transparent background with `Gpt Image 2.5` only, optionally send top-level `"background": "transparent"`; the result is a PNG with an RGBA alpha channel. Do not send this field for video or other image models.
- `POST /videos/generations`: `model`, `prompt`, optional `duration`, `resolution`, `size`, `aspect_ratio`, and model-configured reference fields. Subject references may use `image_urls`, `video_urls`, `audio_urls`, or `video_list`. First/end frames may use `image_with_roles`, `first_frame_image`, and `end_frame_image`; select them strictly from the model configuration.
- `GET /tasks/{task_id}`: send `X-Model-Name: <the model name used for submission>`. The response contains the task status and, when complete, a remote media URL.


The backend accepts a model display name and resolves it to its configured provider model. Task IDs may be returned as `id`, `task_id`, `taskId`, `data.id`, or `data.task_id`. Final media may be nested under `data`, `result`, or `output`, using `url`, `image_url`, `video_url`, `images`, or `videos`.

## Transparent background example

```bash
curl -X POST 'https://www.openflowly.com/v1/images/generations' \
  -H "Authorization: Bearer $OPENFLOWLY_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Gpt Image 2.5",
    "prompt": "A red apple sticker with soft natural shading",
    "n": 1,
    "size": "1:1",
    "quality": "low",
    "background": "transparent"
  }'
```

The endpoint may return a task ID asynchronously; poll `GET /tasks/{task_id}` until the response contains the completed PNG URL.

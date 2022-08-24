# unfurl-cloudmap-exporter

## Requirements

See `.env.sample` for the environment variables needed.

## Start the server

```bash
pip install -r requirements.txt
gunicorn src.app:app -b localhost:8082
```

## Using the server

```http
GET /cloud?url=http%3A%2F%2Fexample.com
```

With the parameter `url` being the URL to a dashboard urlencoded.

from fastapi import Response
from fastapi.responses import StreamingResponse
import json
from typing import Any, Dict, AsyncGenerator

class StreamingJSONResponse(StreamingResponse):
    media_type = "application/json"

    def __init__(
        self,
        content: AsyncGenerator[Dict[str, Any], None],
        status_code: int = 200,
        headers: Dict[str, str] = None,
    ):
        async def generate():
            async for chunk in content:
                yield (json.dumps(chunk) + "\n").encode("utf-8")
        
        super().__init__(
            content=generate(),
            status_code=status_code,
            headers=headers,
            media_type=self.media_type
        )
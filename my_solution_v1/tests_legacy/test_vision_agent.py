import pytest
from unittest.mock import patch, mock_open
from my_solution_v1.rag.vision_agent import describe_image

def test_describe_image_success():
    with patch("my_solution_v1.rag.vision_agent.requests.post") as mock_post, \
         patch("my_solution_v1.rag.vision_agent.encode_image", return_value="base64str"):
        
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Image features a diagram"}}
                ]
            }
        }
        
        desc = describe_image("test.png")
        assert "Image features a diagram" in desc

def test_describe_image_failure():
    with patch("my_solution_v1.rag.vision_agent.requests.post", side_effect=Exception("API Error")), \
         patch("my_solution_v1.rag.vision_agent.encode_image", return_value="base64str"):
         
        desc = describe_image("test.png")
        assert "ОШИБКА" in desc

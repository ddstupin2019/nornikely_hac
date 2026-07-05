import pytest
from unittest.mock import patch
from my_solution_v1.agents.agent_1_parser import parse_user_request
from my_solution_v1.agents.agent_2_generator import generate_hypotheses
from my_solution_v1.agents.agent_3_checker import check_hypothesis
from my_solution_v1.agents.agent_4_ranker import rank_hypotheses

def test_parse_user_request():
    with patch("my_solution_v1.agents.agent_1_parser.call_qwen_llm") as mock_call:
        mock_call.return_value = '{"Проблема": "Тест", "Оборудование": "Печь", "Бюджет": "100", "Дополнительные_ограничения": "Нет"}'
        res = parse_user_request("Тестовый текст", "")
        assert res["Проблема"] == "Тест"

def test_generate_hypotheses():
    with patch("my_solution_v1.agents.agent_2_generator.call_qwen_llm") as mock_call:
        mock_call.return_value = '[{"название": "Г1"}, {"название": "Г2"}]'
        hyps = generate_hypotheses({"Проблема": "П1"}, "", ["ошибка1"])
        assert len(hyps) == 2
        assert hyps[0]["название"] == "Г1"

def test_check_hypothesis():
    with patch("my_solution_v1.agents.agent_3_checker.call_qwen_llm") as mock_call, \
         patch("my_solution_v1.agents.agent_3_checker.vector_store") as mock_vs:
        
        mock_vs.similarity_search.return_value = []
        mock_call.return_value = '{"is_valid": true, "justification": "Хорошо", "sources": ["doc1"]}'
        
        is_valid, validated, feedback = check_hypothesis({"название": "Тест Г1"})
        assert is_valid is True
        assert validated["обоснование"] == "Хорошо"

def test_rank_hypotheses():
    with patch("my_solution_v1.agents.agent_4_ranker.call_qwen_llm") as mock_call:
        mock_call.return_value = '[{"название": "Г1", "итоговая_оценка_от_директора": "Топ"}]'
        ranked = rank_hypotheses([{"название": "Г1"}, {"название": "Г2"}])
        assert len(ranked) == 1
        assert ranked[0]["итоговая_оценка_от_директора"] == "Топ"

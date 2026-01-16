"""Tests for chat parser"""
import pytest
from src.core.parser import parse_enhance_result, parse_chat, extract_gold, extract_level
from src.core.state import EnhanceResult


class TestParseEnhanceResult:
    """Tests for parse_enhance_result function"""

    def test_success_pattern(self):
        """Test success detection"""
        text = "+5강 강화에 성공했습니다!"
        result, level = parse_enhance_result(text)
        assert result == EnhanceResult.SUCCESS
        assert level == 5

    def test_success_with_congratulations(self):
        """Test success with congratulation message"""
        text = "축하합니다! +10강 달성!"
        result, level = parse_enhance_result(text)
        assert result == EnhanceResult.SUCCESS
        assert level == 10

    def test_maintain_pattern(self):
        """Test maintain detection"""
        text = "강화에 실패했습니다. 레벨이 유지됩니다."
        result, level = parse_enhance_result(text)
        assert result == EnhanceResult.MAINTAIN

    def test_destroy_pattern(self):
        """Test destroy detection"""
        text = "강화에 실패하여 검이 파괴되었습니다."
        result, level = parse_enhance_result(text)
        assert result == EnhanceResult.DESTROY
        assert level == 0

    def test_destroy_from_zero(self):
        """Test destroy with restart message"""
        text = "0강부터 다시 시작합니다."
        result, level = parse_enhance_result(text)
        assert result == EnhanceResult.DESTROY
        assert level == 0

    def test_unknown_pattern(self):
        """Test unknown message"""
        text = "안녕하세요"
        result, level = parse_enhance_result(text)
        assert result == EnhanceResult.UNKNOWN
        assert level is None


class TestExtractGold:
    """Tests for gold extraction"""

    def test_gold_with_comma(self):
        """Test gold with comma formatting"""
        text = "현재 골드: 1,000,000원"
        gold = extract_gold(text)
        assert gold == 1000000

    def test_gold_without_comma(self):
        """Test gold without comma"""
        text = "골드: 500원"
        gold = extract_gold(text)
        assert gold == 500

    def test_gold_with_g_suffix(self):
        """Test gold with G suffix"""
        text = "잔액: 50,000G"
        gold = extract_gold(text)
        assert gold == 50000

    def test_no_gold(self):
        """Test text without gold"""
        text = "강화 성공!"
        gold = extract_gold(text)
        assert gold is None


class TestExtractLevel:
    """Tests for level extraction"""

    def test_level_extraction(self):
        """Test level extraction"""
        text = "+15강 검"
        level = extract_level(text)
        assert level == 15

    def test_level_zero(self):
        """Test zero level"""
        text = "+0강 시작"
        level = extract_level(text)
        assert level == 0

    def test_no_level(self):
        """Test text without level"""
        text = "강화 성공"
        level = extract_level(text)
        assert level is None


class TestParseChat:
    """Tests for full chat parsing"""

    def test_full_success_message(self):
        """Test full success message parsing"""
        text = """
        🗡️ +5강 강화에 성공했습니다!
        현재 골드: 50,000원
        """
        result, state = parse_chat(text)
        assert result == EnhanceResult.SUCCESS
        assert state.level == 5
        assert state.gold == 50000

    def test_full_destroy_message(self):
        """Test full destroy message parsing"""
        text = """
        💥 강화에 실패하여 검이 파괴되었습니다.
        0강부터 다시 시작합니다.
        현재 골드: 48,000원
        """
        result, state = parse_chat(text)
        assert result == EnhanceResult.DESTROY
        assert state.level == 0
        assert state.gold == 48000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

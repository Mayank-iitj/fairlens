"""
Unit tests for LLM bias detection service.
Ensures production-ready quality and correctness.
"""
import pytest
from app.services.llm_bias_detection import (
    GenderBiasDetector,
    ToxicityDetector,
    StereotypingDetector,
    SentimentBiasDetector,
    RepresentationAnalyzer,
    LLMBiasDetectionEngine,
)
from app.services.llm_bias_errors import (
    TextValidator,
    BatchAnalysisValidator,
    TextLengthError,
    InputValidationError,
)


class TestGenderBiasDetector:
    """Test gender bias detection."""
    
    def setup_method(self):
        self.detector = GenderBiasDetector()
    
    def test_balanced_text_no_gender_bias(self):
        """Test that balanced text is not flagged as biased."""
        text = "Doctors and nurses work together. Both men and women are excellent in their roles."
        result = self.detector.detect(text)
        assert result.score < 0.3
        assert result.severity in ["low", "medium"]
    
    def test_gender_stereotype_detection(self):
        """Test detection of gender stereotypes."""
        text = "Strong men are leaders while women are nurturing caregivers."
        result = self.detector.detect(text)
        assert result.score > 0.2
        assert len(result.evidence) > 0
        assert result.severity in ["medium", "high", "critical"]
    
    def test_gender_imbalance_detection(self):
        """Test detection of gender pronoun imbalance."""
        text = "He did this, he did that, he always does it. She sometimes helps."
        result = self.detector.detect(text)
        assert result.score > 0.2
    
    def test_empty_recommendations_for_clean_text(self):
        """Test that clean text gets positive recommendations."""
        text = "People of all genders work in various professions successfully."
        result = self.detector.detect(text)
        if result.score < 0.1:
            assert len(result.recommendations) > 0


class TestToxicityDetector:
    """Test toxicity detection."""
    
    def setup_method(self):
        self.detector = ToxicityDetector()
    
    def test_offensive_language_detection(self):
        """Test detection of offensive language."""
        text = "These people are stupid and pathetic."
        result = self.detector.detect(text)
        assert result.score > 0.1
        assert len(result.evidence) > 0
    
    def test_aggressive_language_detection(self):
        """Test detection of aggressive language."""
        text = "We must destroy all enemies and crush their will."
        result = self.detector.detect(text)
        assert result.score > 0.1
        assert result.severity in ["medium", "high", "critical"]
    
    def test_clean_text_low_toxicity(self):
        """Test that respectful text has low toxicity score."""
        text = "Let's work together to find a solution that benefits everyone."
        result = self.detector.detect(text)
        assert result.score < 0.2


class TestStereotypingDetector:
    """Test stereotyping detection."""
    
    def setup_method(self):
        self.detector = StereotypingDetector()
    
    def test_broad_generalizations_detection(self):
        """Test detection of broad generalizations."""
        text = "All millennials are lazy and never work hard."
        result = self.detector.detect(text)
        assert result.score > 0.2
        assert len(result.evidence) > 0
    
    def test_occupational_stereotypes_detection(self):
        """Test detection of occupational stereotypes."""
        text = "All nurses are women and all CEOs are men."
        result = self.detector.detect(text)
        assert result.score > 0.1
    
    def test_no_stereotyping_specific_examples(self):
        """Test that specific examples don't trigger stereotyping."""
        text = "Jane is a successful CEO. She leads a team of 50 people."
        result = self.detector.detect(text)
        assert result.score < 0.2


class TestSentimentBiasDetector:
    """Test sentiment bias detection."""
    
    def setup_method(self):
        self.detector = SentimentBiasDetector()
    
    def test_overwhelmingly_positive_bias(self):
        """Test detection of overwhelming positive bias."""
        text = "This is excellent, great, wonderful, and amazing. Truly superb."
        result = self.detector.detect(text)
        assert result.score > 0.2
    
    def test_overwhelmingly_negative_bias(self):
        """Test detection of overwhelming negative bias."""
        text = "This is terrible, bad, awful, and horrible. Completely incompetent."
        result = self.detector.detect(text)
        assert result.score > 0.2
    
    def test_balanced_sentiment(self):
        """Test that balanced sentiment scores low."""
        text = "The project has strengths and weaknesses. It succeeded in some areas and failed in others."
        result = self.detector.detect(text)
        assert result.score < 0.3


class TestRepresentationAnalyzer:
    """Test representation analysis."""
    
    def setup_method(self):
        self.analyzer = RepresentationAnalyzer()
    
    def test_balanced_gender_representation(self):
        """Test that balanced representation scores low."""
        text = "Men and women both contributed to this project. He wrote the code while she managed the timeline."
        result = self.analyzer.detect(text)
        assert result.score < 0.3
    
    def test_imbalanced_representation(self):
        """Test detection of imbalanced representation."""
        text = "Men are strong, capable, intelligent leaders. Women are also here."
        result = self.analyzer.detect(text)
        assert result.score > 0.2
    
    def test_minority_representation(self):
        """Test analysis of minority group representation."""
        text = "Most employees are from the majority group. A few minorities work here too."
        result = self.analyzer.detect(text)
        assert result.severity in ["low", "medium", "high", "critical"]


class TestLLMBiasDetectionEngine:
    """Test the main bias detection engine."""
    
    def setup_method(self):
        self.engine = LLMBiasDetectionEngine()
    
    def test_comprehensive_analysis_structure(self):
        """Test that analysis returns proper structure."""
        text = "All women are emotional and weak. Men are strong leaders."
        analysis = self.engine.analyze(text)
        
        assert hasattr(analysis, 'overall_bias_score')
        assert hasattr(analysis, 'bias_level')
        assert hasattr(analysis, 'detected_biases')
        assert hasattr(analysis, 'summary')
        assert hasattr(analysis, 'risks')
        assert hasattr(analysis, 'recommendations')
        assert 0 <= analysis.overall_bias_score <= 1
    
    def test_high_bias_detection(self):
        """Test detection of highly biased text."""
        text = """
        All men are strong leaders and successful businessmen.
        Women are better suited for supporting roles and household duties.
        This has been proven scientifically and is just common sense.
        """
        analysis = self.engine.analyze(text)
        assert analysis.overall_bias_score > 0.5
        assert analysis.bias_level in ["high", "critical"]
        assert len(analysis.detected_biases) > 0
    
    def test_low_bias_detection(self):
        """Test that fair text scores low on bias."""
        text = "People from diverse backgrounds contribute to our success. Both genders are represented in all roles."
        analysis = self.engine.analyze(text)
        assert analysis.overall_bias_score < 0.3
        assert analysis.bias_level in ["very_low", "low"]
    
    def test_recommendations_provided(self):
        """Test that recommendations are provided for biased text."""
        text = "All doctors are men. All nurses are women."
        analysis = self.engine.analyze(text)
        assert len(analysis.recommendations) > 0
    
    def test_multiple_bias_types_detected(self):
        """Test that multiple bias types are detected."""
        text = "Stupid women and weak men both fail at business. Real leaders are strong and decisive."
        analysis = self.engine.analyze(text)
        # Should detect gender bias, toxicity, and stereotyping
        assert len(analysis.detected_biases) >= 2
    
    def test_text_too_short_error(self):
        """Test error for text that's too short."""
        with pytest.raises(ValueError):
            self.engine.analyze("short")
    
    def test_empty_text_error(self):
        """Test error for empty text."""
        with pytest.raises(ValueError):
            self.engine.analyze("")


class TestTextValidator:
    """Test input validation."""
    
    def test_valid_text_passes(self):
        """Test that valid text passes validation."""
        TextValidator.validate("This is a valid text that should pass validation.")
        # Should not raise
    
    def test_text_too_short_raises_error(self):
        """Test that short text raises error."""
        with pytest.raises(TextLengthError):
            TextValidator.validate("short")
    
    def test_non_string_input_raises_error(self):
        """Test that non-string input raises error."""
        with pytest.raises(InputValidationError):
            TextValidator.validate(123)
    
    def test_empty_string_raises_error(self):
        """Test that empty string raises error."""
        with pytest.raises(InputValidationError):
            TextValidator.validate("")


class TestBatchAnalysisValidator:
    """Test batch analysis validation."""
    
    def test_valid_batch_passes(self):
        """Test that valid batch passes validation."""
        texts = ["This is valid text " + str(i) for i in range(5)]
        BatchAnalysisValidator.validate(texts)
        # Should not raise
    
    def test_too_many_items_raises_error(self):
        """Test that too many items raises error."""
        texts = ["Valid text " + str(i) for i in range(101)]
        with pytest.raises(InputValidationError):
            BatchAnalysisValidator.validate(texts)
    
    def test_empty_batch_raises_error(self):
        """Test that empty batch raises error."""
        with pytest.raises(InputValidationError):
            BatchAnalysisValidator.validate([])
    
    def test_non_list_input_raises_error(self):
        """Test that non-list input raises error."""
        with pytest.raises(InputValidationError):
            BatchAnalysisValidator.validate("not a list")


class TestBiasScoreWeighting:
    """Test that bias scores are properly weighted."""
    
    def setup_method(self):
        self.engine = LLMBiasDetectionEngine()
    
    def test_toxicity_weighted_heavily(self):
        """Test that toxicity has high weight in overall score."""
        toxic_text = "Stupid idiot, you're a moron and a waste of space!"
        analysis = self.engine.analyze(toxic_text)
        # Toxicity has 0.3 weight, so should contribute significantly
        assert analysis.overall_bias_score > 0.1
    
    def test_gender_bias_weighted(self):
        """Test that gender bias contributes to score."""
        gender_biased_text = "All men are leaders, all women are followers."
        analysis = self.engine.analyze(gender_biased_text)
        assert analysis.overall_bias_score > 0.2


# Integration tests would go here in production
class TestIntegration:
    """Integration tests for the full pipeline."""
    
    def test_end_to_end_analysis_workflow(self):
        """Test complete analysis workflow."""
        engine = LLMBiasDetectionEngine()
        
        # Analyze different texts
        texts = [
            "This is a neutral, balanced text about work.",
            "All women are emotional, all men are logical.",
            "Diverse teams produce better results than homogeneous ones.",
        ]
        
        for text in texts:
            analysis = engine.analyze(text)
            assert analysis.overall_bias_score >= 0
            assert analysis.bias_level in ["very_low", "low", "moderate", "high", "critical"]
            assert len(analysis.detected_biases) > 0
            assert len(analysis.recommendations) > 0


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
LLM Bias Detection Service
Production-ready algorithms for detecting bias in Large Language Model outputs.
Implements multiple complementary algorithms for comprehensive bias analysis.
"""
import json
import logging
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class BiasCategory(Enum):
    """Categories of bias that can be detected."""
    GENDER = "gender"
    RACIAL = "racial"
    AGE = "age"
    SENTIMENT = "sentiment"
    TOXICITY = "toxicity"
    STEREOTYPING = "stereotyping"
    REPRESENTATION = "representation"
    FAIRNESS = "fairness"


@dataclass
class BiasDetectionResult:
    """Result from a single bias detection algorithm."""
    algorithm: str
    category: str
    score: float  # 0-1, where 1 is highest bias
    severity: str  # "low", "medium", "high", "critical"
    description: str
    evidence: List[str]
    recommendations: List[str]


@dataclass
class ComprehensiveBiasAnalysis:
    """Complete bias analysis result."""
    text: str
    timestamp: str
    overall_bias_score: float  # 0-1
    bias_level: str  # "very_low", "low", "moderate", "high", "critical"
    detected_biases: List[BiasDetectionResult]
    summary: str
    risks: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]


class GenderBiasDetector:
    """Detects gender-based bias and stereotyping in text."""
    
    # Gender-associated words and stereotypes
    GENDER_STEREOTYPES = {
        "male": {
            "positive": ["strong", "leader", "logical", "ambitious", "confident", "competitive"],
            "negative": ["aggressive", "emotional", "weak", "timid"],
            "occupations": ["CEO", "engineer", "programmer", "doctor", "manager"],
            "attributes": ["handsome", "masculine", "athletic"],
        },
        "female": {
            "positive": ["nurturing", "caring", "empathetic", "creative", "supportive"],
            "negative": ["emotional", "weak", "sensitive", "dependent", "irrational"],
            "occupations": ["nurse", "teacher", "secretary", "receptionist"],
            "attributes": ["beautiful", "feminine", "graceful"],
        },
    }
    
    GENDER_PRONOUNS = {
        "he": "male", "him": "male", "his": "male", "himself": "male",
        "she": "female", "her": "female", "hers": "female", "herself": "female",
    }
    
    def detect(self, text: str) -> BiasDetectionResult:
        """Detect gender bias in text."""
        text_lower = text.lower()
        
        gender_mentions = {"male": 0, "female": 0}
        male_stereotypes = 0
        female_stereotypes = 0
        evidence = []
        
        # Count gender pronouns
        for pronoun, gender in self.GENDER_PRONOUNS.items():
            count = len(re.findall(r"\b" + pronoun + r"\b", text_lower))
            gender_mentions[gender] += count
            if count > 0:
                evidence.append(f"Found {pronoun} ({count} times)")
        
        # Detect stereotypical language
        for gender, stereotypes in self.GENDER_STEREOTYPES.items():
            for category, words in stereotypes.items():
                for word in words:
                    if re.search(r"\b" + word + r"\b", text_lower):
                        if gender == "male":
                            male_stereotypes += 1
                        else:
                            female_stereotypes += 1
                        evidence.append(f"Stereotypical {gender} language: '{word}'")
        
        # Calculate gender imbalance score
        total_mentions = sum(gender_mentions.values())
        gender_imbalance = 0.0
        
        if total_mentions > 0:
            male_ratio = gender_mentions["male"] / total_mentions
            female_ratio = gender_mentions["female"] / total_mentions
            
            # If one gender is heavily favored (>70%), flag as imbalance
            if male_ratio > 0.7 or female_ratio > 0.7:
                gender_imbalance = abs(male_ratio - female_ratio)
        
        # Calculate stereotyping score
        stereotype_score = (male_stereotypes + female_stereotypes) / max(len(text.split()), 1)
        stereotype_score = min(stereotype_score * 2, 1.0)  # Normalize to 0-1
        
        # Overall gender bias score
        overall_score = (gender_imbalance + stereotype_score) / 2
        
        severity = self._severity_from_score(overall_score)
        
        recommendations = []
        if gender_imbalance > 0.5:
            recommendations.append("Ensure balanced representation of genders in content")
            recommendations.append("Review text for male/female pronoun imbalance")
        
        if stereotype_score > 0.3:
            recommendations.append("Avoid stereotypical language when describing genders")
            recommendations.append("Use diverse examples for both men and women")
        
        return BiasDetectionResult(
            algorithm="gender_bias_detector",
            category=BiasCategory.GENDER.value,
            score=overall_score,
            severity=severity,
            description=f"Detected gender bias: imbalance={gender_imbalance:.2f}, stereotyping={stereotype_score:.2f}",
            evidence=evidence[:5] if evidence else ["No obvious gender bias indicators found"],
            recommendations=recommendations or ["Content appears gender-balanced"],
        )
    
    @staticmethod
    def _severity_from_score(score: float) -> str:
        """Convert bias score to severity level."""
        if score < 0.1:
            return "low"
        elif score < 0.3:
            return "medium"
        elif score < 0.6:
            return "high"
        else:
            return "critical"


class ToxicityDetector:
    """Detects toxic, offensive, and hateful language."""
    
    TOXIC_PATTERNS = {
        "offensive": [
            r"\b(stupid|idiots?|dumb|moron|retard|crazy)\b",
            r"\b(waste|useless|pathetic)\b",
        ],
        "hate_speech": [
            r"\b(should|deserve|need to)\s+(be|get|are)\s+(killed?|murdered|hurt|attack)",
            r"\b(ban|exclude|eliminate)\s+(all\s+)?(men|women|\w+ians?|people)",
        ],
        "dehumanizing": [
            r"\b(animals?|monsters?|vermin|scum)\b.*\b(people|group|community)\b",
            r"\b(people|group|community).*\b(animals?|monsters?|vermin|scum)\b",
        ],
        "slurs": [
            # Placeholder - real implementation would have comprehensive list
            r"(?i)\b(badword1|badword2)\b"
        ],
    }
    
    def detect(self, text: str) -> BiasDetectionResult:
        """Detect toxic language in text."""
        found_toxicity = []
        toxic_score = 0.0
        evidence = []
        
        text_lower = text.lower()
        
        for category, patterns in self.TOXIC_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    found_toxicity.append(category)
                    toxic_score += 0.15  # Each match adds to score
                    evidence.append(f"{category}: '{match.group()}'")
        
        # Normalize score to 0-1
        toxic_score = min(toxic_score, 1.0)
        
        # Check for aggressive tone using sentiment
        aggressive_words = ["must", "destroy", "eliminate", "annihilate", "crush", "kill"]
        for word in aggressive_words:
            if re.search(r"\b" + word + r"\b", text_lower):
                toxic_score += 0.1
                evidence.append(f"Aggressive language: '{word}'")
        
        toxic_score = min(toxic_score, 1.0)
        
        severity = self._severity_from_score(toxic_score)
        
        recommendations = []
        if toxic_score > 0.2:
            recommendations.append("Remove offensive or dehumanizing language")
            recommendations.append("Use respectful and inclusive terminology")
            recommendations.append("Avoid aggressive or threatening language")
        
        return BiasDetectionResult(
            algorithm="toxicity_detector",
            category=BiasCategory.TOXICITY.value,
            score=toxic_score,
            severity=severity,
            description=f"Toxicity detected in text (score: {toxic_score:.2f})",
            evidence=evidence[:5] if evidence else ["No significant toxicity detected"],
            recommendations=recommendations or ["Text appears respectful and non-toxic"],
        )
    
    @staticmethod
    def _severity_from_score(score: float) -> str:
        """Convert toxicity score to severity level."""
        if score < 0.1:
            return "low"
        elif score < 0.25:
            return "medium"
        elif score < 0.5:
            return "high"
        else:
            return "critical"


class StereotypingDetector:
    """Detects stereotypical thinking and generalizations."""
    
    STEREOTYPE_PATTERNS = {
        "broad_generalizations": [
            r"\b(all|every|all of the)\s+(\w+)\s+(are|is|always|never)",
            r"\b(\w+)\s+(always|never|all)\s+(are|is|does|do)",
        ],
        "occupational_stereotypes": [
            r"\b(doctor|nurse|CEO|secretary|janitor|cook)\b.*\b(man|woman|male|female)\b",
        ],
        "age_stereotypes": [
            r"\b(old people|elderly|millennials?|gen z|boomers?)\s+(are|is)\s+\w+",
            r"\b(old|young|elderly)\b.*\b(technology|modern|traditional)\b",
        ],
        "cultural_stereotypes": [
            r"\b(typically|usually|normally)\s+\w+\s+(people|men|women|group|community)\b",
        ],
    }
    
    def detect(self, text: str) -> BiasDetectionResult:
        """Detect stereotypical thinking."""
        stereotype_matches = []
        stereotype_score = 0.0
        evidence = []
        
        for category, patterns in self.STEREOTYPE_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    stereotype_matches.append(category)
                    stereotype_score += 0.2
                    evidence.append(f"{category}: '{match.group()}'")
        
        stereotype_score = min(stereotype_score, 1.0)
        
        severity = self._severity_from_score(stereotype_score)
        
        recommendations = []
        if stereotype_score > 0.2:
            recommendations.append("Avoid broad generalizations about groups")
            recommendations.append("Use specific examples rather than stereotypes")
            recommendations.append("Acknowledge diversity within groups")
        
        return BiasDetectionResult(
            algorithm="stereotyping_detector",
            category=BiasCategory.STEREOTYPING.value,
            score=stereotype_score,
            severity=severity,
            description=f"Stereotypical language detected (score: {stereotype_score:.2f})",
            evidence=evidence[:5] if evidence else ["No obvious stereotyping detected"],
            recommendations=recommendations or ["Text avoids stereotypical generalizations"],
        )
    
    @staticmethod
    def _severity_from_score(score: float) -> str:
        """Convert stereotype score to severity level."""
        if score < 0.1:
            return "low"
        elif score < 0.25:
            return "medium"
        elif score < 0.5:
            return "high"
        else:
            return "critical"


class SentimentBiasDetector:
    """Detects sentiment bias toward different groups or concepts."""
    
    # Sentiment associations
    POSITIVE_WORDS = [
        "good", "great", "excellent", "smart", "intelligent", "capable",
        "strong", "reliable", "trustworthy", "honest", "successful", "beautiful"
    ]
    
    NEGATIVE_WORDS = [
        "bad", "poor", "terrible", "stupid", "weak", "unreliable",
        "untrustworthy", "dishonest", "failed", "ugly", "incompetent"
    ]
    
    def detect(self, text: str) -> BiasDetectionResult:
        """Detect sentiment bias in text."""
        text_lower = text.lower()
        
        positive_count = 0
        negative_count = 0
        
        for word in self.POSITIVE_WORDS:
            positive_count += len(re.findall(r"\b" + word + r"\b", text_lower))
        
        for word in self.NEGATIVE_WORDS:
            negative_count += len(re.findall(r"\b" + word + r"\b", text_lower))
        
        total_sentiment_words = positive_count + negative_count
        
        sentiment_bias = 0.0
        evidence = []
        
        if total_sentiment_words > 0:
            positive_ratio = positive_count / total_sentiment_words
            negative_ratio = negative_count / total_sentiment_words
            
            # Strong positive or negative bias is problematic
            if positive_ratio > 0.75:
                sentiment_bias = 0.6
                evidence.append(f"Overwhelmingly positive sentiment ({positive_ratio:.1%})")
            elif negative_ratio > 0.75:
                sentiment_bias = 0.6
                evidence.append(f"Overwhelmingly negative sentiment ({negative_ratio:.1%})")
            elif abs(positive_ratio - 0.5) > 0.3:
                sentiment_bias = 0.3
                evidence.append(f"Skewed sentiment: {positive_ratio:.1%} positive, {negative_ratio:.1%} negative")
        
        severity = self._severity_from_score(sentiment_bias)
        
        recommendations = []
        if sentiment_bias > 0.2:
            recommendations.append("Balance positive and negative descriptions")
            recommendations.append("Use objective, neutral language")
            recommendations.append("Provide fair assessment of strengths and weaknesses")
        
        return BiasDetectionResult(
            algorithm="sentiment_bias_detector",
            category=BiasCategory.SENTIMENT.value,
            score=sentiment_bias,
            severity=severity,
            description=f"Sentiment bias detected (score: {sentiment_bias:.2f})",
            evidence=evidence or ["Sentiment appears balanced"],
            recommendations=recommendations or ["Sentiment appears balanced and fair"],
        )
    
    @staticmethod
    def _severity_from_score(score: float) -> str:
        """Convert sentiment bias score to severity level."""
        if score < 0.1:
            return "low"
        elif score < 0.3:
            return "medium"
        elif score < 0.5:
            return "high"
        else:
            return "critical"


class RepresentationAnalyzer:
    """Analyzes representation of groups and topics."""
    
    def detect(self, text: str) -> BiasDetectionResult:
        """Analyze representation in text."""
        text_lower = text.lower()
        words = text_lower.split()
        
        # Count mentions of different groups
        group_mentions = {
            "men": len(re.findall(r"\b(man|men|boy|boys|male|males)\b", text_lower)),
            "women": len(re.findall(r"\b(woman|women|girl|girls|female|females)\b", text_lower)),
            "minorities": len(re.findall(r"\b(minority|minorities|diverse|diversity|ethnic|race)\b", text_lower)),
            "positive_descriptors": 0,
            "negative_descriptors": 0,
        }
        
        # Count positive/negative descriptors
        positive_words = ["good", "great", "excellent", "smart", "capable", "successful"]
        negative_words = ["bad", "poor", "weak", "incompetent", "failed"]
        
        for word in positive_words:
            group_mentions["positive_descriptors"] += len(re.findall(r"\b" + word + r"\b", text_lower))
        
        for word in negative_words:
            group_mentions["negative_descriptors"] += len(re.findall(r"\b" + word + r"\b", text_lower))
        
        # Calculate representation imbalance
        men_mentions = group_mentions["men"]
        women_mentions = group_mentions["women"]
        
        representation_score = 0.0
        evidence = []
        
        total_group_mentions = men_mentions + women_mentions
        if total_group_mentions > 0:
            men_ratio = men_mentions / total_group_mentions
            women_ratio = women_mentions / total_group_mentions
            
            if men_ratio > 0.7 or women_ratio > 0.7:
                representation_score = abs(men_ratio - women_ratio)
                evidence.append(f"Imbalanced representation: men={men_ratio:.1%}, women={women_ratio:.1%}")
        
        # Check for positive/negative bias in descriptors
        total_descriptors = group_mentions["positive_descriptors"] + group_mentions["negative_descriptors"]
        if total_descriptors > 0:
            positive_ratio = group_mentions["positive_descriptors"] / total_descriptors
            if positive_ratio > 0.7 or positive_ratio < 0.3:
                representation_score = max(representation_score, abs(positive_ratio - 0.5))
                evidence.append(f"Descriptor bias: {positive_ratio:.1%} positive")
        
        representation_score = min(representation_score, 1.0)
        severity = self._severity_from_score(representation_score)
        
        recommendations = []
        if representation_score > 0.2:
            recommendations.append("Ensure balanced representation across groups")
            recommendations.append("Represent groups with diverse characteristics")
            recommendations.append("Avoid concentrating positive or negative attributes")
        
        return BiasDetectionResult(
            algorithm="representation_analyzer",
            category=BiasCategory.REPRESENTATION.value,
            score=representation_score,
            severity=severity,
            description=f"Representation imbalance detected (score: {representation_score:.2f})",
            evidence=evidence or ["Representation appears balanced"],
            recommendations=recommendations or ["Representation appears fair and balanced"],
        )
    
    @staticmethod
    def _severity_from_score(score: float) -> str:
        """Convert representation score to severity level."""
        if score < 0.1:
            return "low"
        elif score < 0.3:
            return "medium"
        elif score < 0.5:
            return "high"
        else:
            return "critical"


class LLMBiasDetectionEngine:
    """Main engine for comprehensive LLM bias detection."""
    
    def __init__(self):
        """Initialize all bias detectors."""
        self.gender_detector = GenderBiasDetector()
        self.toxicity_detector = ToxicityDetector()
        self.stereotyping_detector = StereotypingDetector()
        self.sentiment_detector = SentimentBiasDetector()
        self.representation_analyzer = RepresentationAnalyzer()
        
        logger.info("LLM Bias Detection Engine initialized with all detectors")
    
    def analyze(self, text: str) -> ComprehensiveBiasAnalysis:
        """
        Perform comprehensive bias analysis on LLM output.
        
        Args:
            text: The LLM output text to analyze
            
        Returns:
            ComprehensiveBiasAnalysis with all detected biases
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not isinstance(text, str):
            raise ValueError("Input text must be a non-empty string")
        
        if len(text.strip()) < 10:
            raise ValueError("Input text must be at least 10 characters long")
        
        from datetime import datetime
        
        # Run all detectors
        detections = [
            self.gender_detector.detect(text),
            self.toxicity_detector.detect(text),
            self.stereotyping_detector.detect(text),
            self.sentiment_detector.detect(text),
            self.representation_analyzer.detect(text),
        ]
        
        # Calculate overall bias score (weighted average)
        weights = {
            "gender_bias_detector": 0.2,
            "toxicity_detector": 0.3,
            "stereotyping_detector": 0.2,
            "sentiment_bias_detector": 0.15,
            "representation_analyzer": 0.15,
        }
        
        weighted_score = sum(
            detection.score * weights.get(detection.algorithm, 0.2)
            for detection in detections
        )
        
        overall_bias_score = weighted_score
        
        # Determine overall bias level
        if overall_bias_score < 0.15:
            bias_level = "very_low"
        elif overall_bias_score < 0.3:
            bias_level = "low"
        elif overall_bias_score < 0.5:
            bias_level = "moderate"
        elif overall_bias_score < 0.7:
            bias_level = "high"
        else:
            bias_level = "critical"
        
        # Collect all risks and recommendations
        all_risks = []
        all_recommendations = []
        
        for detection in detections:
            if detection.score > 0.2:  # Only include significant biases
                all_risks.append(f"{detection.category}: {detection.description}")
            all_recommendations.extend(detection.recommendations)
        
        # Generate summary
        summary = self._generate_summary(detections, overall_bias_score)
        
        # Remove duplicates from recommendations
        all_recommendations = list(set(all_recommendations))
        
        return ComprehensiveBiasAnalysis(
            text=text,
            timestamp=datetime.utcnow().isoformat(),
            overall_bias_score=overall_bias_score,
            bias_level=bias_level,
            detected_biases=detections,
            summary=summary,
            risks=all_risks or ["No significant biases detected"],
            recommendations=all_recommendations or ["Content appears fair and unbiased"],
            metadata={
                "text_length": len(text),
                "word_count": len(text.split()),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    def _generate_summary(detections: List[BiasDetectionResult], overall_score: float) -> str:
        """Generate a human-readable summary of the analysis."""
        critical_biases = [d for d in detections if d.severity == "critical"]
        high_biases = [d for d in detections if d.severity == "high"]
        
        if not critical_biases and not high_biases:
            return "The analyzed text shows no significant biases. Overall bias level is low."
        
        summary_parts = [f"Overall bias score: {overall_score:.2f}"]
        
        if critical_biases:
            bias_types = ", ".join(d.category for d in critical_biases)
            summary_parts.append(f"Critical biases detected: {bias_types}")
        
        if high_biases:
            bias_types = ", ".join(d.category for d in high_biases)
            summary_parts.append(f"High-level biases detected: {bias_types}")
        
        return ". ".join(summary_parts)

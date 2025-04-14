"""
Skill Matching Module for JobMatch

This module provides advanced AI-powered matching between job requirements and candidate skills.
It uses NLP techniques to compute semantic similarity and provide accurate match scores.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download necessary NLTK data (uncomment on first run)
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')

class SkillMatcher:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.vectorizer = TfidfVectorizer(min_df=1, stop_words='english')
        
        # Common skills with synonyms for better matching
        self.skill_synonyms = {
            'python': ['python', 'py', 'python3'],
            'javascript': ['javascript', 'js', 'ecmascript', 'node.js', 'nodejs'],
            'react': ['react', 'reactjs', 'react.js'],
            'sql': ['sql', 'mysql', 'postgresql', 'oracle', 'database'],
            'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence'],
            'data analysis': ['data analysis', 'data analytics', 'business analytics'],
            'project management': ['project management', 'pm', 'project lead', 'project leadership'],
        }
    
    def preprocess_text(self, text):
        """Preprocess text by tokenizing, removing stop words, and lemmatizing"""
        tokens = nltk.word_tokenize(text.lower())
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in self.stop_words]
        return ' '.join(tokens)
    
    def expand_skills(self, skills_list):
        """Expand skills with their synonyms for better matching"""
        expanded_skills = []
        for skill in skills_list:
            skill_lower = skill.lower()
            expanded_skills.append(skill)
            
            # Add synonyms if available
            for key, synonyms in self.skill_synonyms.items():
                if skill_lower in synonyms or skill_lower == key:
                    expanded_skills.extend(synonyms)
        
        return list(set(expanded_skills))  # Remove duplicates
    
    def calculate_match_score(self, candidate_skills, job_requirements, experience_weight=0.3):
        """
        Calculate match score between candidate skills and job requirements
        
        Args:
            candidate_skills (list): List of candidate's skills
            job_requirements (list): List of job requirements/skills
            experience_weight (float): Weight for experience in scoring (0.0-1.0)
            
        Returns:
            float: Match score between 0 and 1
        """
        # Expand skills with synonyms
        expanded_candidate_skills = self.expand_skills(candidate_skills)
        expanded_job_requirements = self.expand_skills(job_requirements)
        
        # Convert lists to strings for vectorization
        candidate_text = ' '.join(expanded_candidate_skills)
        job_text = ' '.join(expanded_job_requirements)
        
        # Preprocess 
        candidate_processed = self.preprocess_text(candidate_text)
        job_processed = self.preprocess_text(job_text)
        
        # Create TF-IDF matrix
        try:
            tfidf_matrix = self.vectorizer.fit_transform([candidate_processed, job_processed])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Basic match score
            if similarity < 0:  # Handle negative similarity values
                match_score = 0
            else:
                match_score = similarity
            
            return round(match_score, 2)
        except:
            # Fallback to a simpler matching approach if vectorization fails
            common_skills = set(expanded_candidate_skills).intersection(set(expanded_job_requirements))
            if not job_requirements:
                return 0
            return round(len(common_skills) / len(job_requirements), 2)
    
    def get_missing_skills(self, candidate_skills, job_requirements):
        """
        Identify skills missing from the candidate's profile
        
        Args:
            candidate_skills (list): List of candidate's skills
            job_requirements (list): List of job requirements/skills
            
        Returns:
            list: Skills missing from candidate's profile
        """
        # Expand skills with synonyms
        expanded_candidate_skills = self.expand_skills(candidate_skills)
        expanded_job_requirements = self.expand_skills(job_requirements)
        
        # Create sets for comparison
        candidate_skills_set = set(s.lower() for s in expanded_candidate_skills)
        job_skills_set = set(s.lower() for s in expanded_job_requirements)
        
        # Find missing skills
        missing_skills = job_skills_set - candidate_skills_set
        
        # Convert back to original job requirement format (not synonyms)
        original_missing = []
        for skill in job_requirements:
            if skill.lower() in missing_skills:
                original_missing.append(skill)
        
        return original_missing
    
    def get_match_details(self, candidate_skills, job_requirements, candidate_experience=None, job_experience=None):
        """
        Get comprehensive match details including score and missing skills
        
        Args:
            candidate_skills (list): List of candidate's skills
            job_requirements (list): List of job requirements/skills
            candidate_experience (int, optional): Candidate's years of experience
            job_experience (int, optional): Required years of experience
            
        Returns:
            dict: Match details including score, missing skills, etc.
        """
        match_score = self.calculate_match_score(candidate_skills, job_requirements)
        missing_skills = self.get_missing_skills(candidate_skills, job_requirements)
        
        # Experience match calculation
        experience_match = 1.0
        if candidate_experience is not None and job_experience is not None and job_experience > 0:
            experience_match = min(candidate_experience / job_experience, 1.0)
        
        # Weighted score
        weighted_score = 0.7 * match_score + 0.3 * experience_match
        
        return {
            'match_score': match_score,
            'match_percentage': int(match_score * 100),
            'missing_skills': missing_skills,
            'experience_match': round(experience_match, 2),
            'weighted_score': round(weighted_score, 2),
            'weighted_percentage': int(weighted_score * 100)
        }


# Helper function to use the matcher
def get_job_match(candidate_skills, job_skills, candidate_exp=None, job_exp=None):
    """
    Helper function to get job match score and details
    
    Args:
        candidate_skills (list): List of candidate's skills
        job_skills (list): List of job requirements/skills
        candidate_exp (int, optional): Candidate's years of experience
        job_exp (int, optional): Required years of experience
        
    Returns:
        dict: Match details
    """
    matcher = SkillMatcher()
    return matcher.get_match_details(candidate_skills, job_skills, candidate_exp, job_exp) 
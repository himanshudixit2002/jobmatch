"""
Skill Analysis and Learning Recommendations for JobMatch

This module analyzes skill gaps between candidate profiles and job requirements,
then provides learning recommendations to help candidates improve their skills.
"""

import requests
from app.utils.matching import SkillMatcher

class SkillGapAnalyzer:
    def __init__(self):
        self.skill_matcher = SkillMatcher()
        
        # Map skills to general categories for better course recommendations
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin'],
            'web_development': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'node.js', 'django', 'flask'],
            'data_science': ['python', 'r', 'sql', 'machine learning', 'data analysis', 'statistics', 'pandas', 'numpy'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'ci/cd', 'terraform'],
            'design': ['ui', 'ux', 'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd'],
            'project_management': ['agile', 'scrum', 'kanban', 'jira', 'project management'],
        }
        
        # Popular learning platforms and their base URLs
        self.learning_platforms = {
            'coursera': 'https://www.coursera.org/courses?query=',
            'udemy': 'https://www.udemy.com/courses/search/?src=ukw&q=',
            'pluralsight': 'https://www.pluralsight.com/search?q=',
            'linkedin': 'https://www.linkedin.com/learning/search?keywords=',
            'edx': 'https://www.edx.org/search?q='
        }
    
    def analyze_skill_gaps(self, user_skills, job_skills):
        """
        Analyze skill gaps between user skills and job requirements
        
        Args:
            user_skills (list): List of user's skills
            job_skills (list): List of job requirements/skills
            
        Returns:
            dict: Skill gap analysis including missing skills and categorization
        """
        # Get missing skills using the SkillMatcher
        missing_skills = self.skill_matcher.get_missing_skills(user_skills, job_skills)
        
        # Categorize missing skills
        categorized_skills = self._categorize_skills(missing_skills)
        
        # Calculate skill gap percentage
        gap_percentage = 0
        if job_skills:
            gap_percentage = (len(missing_skills) / len(job_skills)) * 100
        
        return {
            'missing_skills': missing_skills,
            'categorized_skills': categorized_skills,
            'gap_percentage': round(gap_percentage, 1),
            'total_missing': len(missing_skills),
            'total_required': len(job_skills) if job_skills else 0
        }
    
    def _categorize_skills(self, skills):
        """
        Categorize skills into predefined categories
        
        Args:
            skills (list): List of skills to categorize
            
        Returns:
            dict: Skills organized by category
        """
        categorized = {}
        
        for skill in skills:
            skill_lower = skill.lower()
            assigned = False
            
            # Check which category the skill belongs to
            for category, category_skills in self.skill_categories.items():
                for cat_skill in category_skills:
                    if cat_skill in skill_lower or skill_lower in cat_skill:
                        if category not in categorized:
                            categorized[category] = []
                        categorized[category].append(skill)
                        assigned = True
                        break
                if assigned:
                    break
            
            # For uncategorized skills
            if not assigned:
                if 'other' not in categorized:
                    categorized['other'] = []
                categorized['other'].append(skill)
        
        return categorized
    
    def get_learning_recommendations(self, missing_skills, limit=3):
        """
        Get learning recommendations for missing skills
        
        Args:
            missing_skills (list): List of missing skills
            limit (int): Maximum number of recommendations per skill
            
        Returns:
            dict: Learning recommendations by skill
        """
        recommendations = {}
        
        for skill in missing_skills:
            skill_courses = self._get_courses_for_skill(skill, limit)
            if skill_courses:
                recommendations[skill] = skill_courses
        
        return recommendations
    
    def _get_courses_for_skill(self, skill, limit=3):
        """
        Generate course recommendations for a specific skill
        
        Args:
            skill (str): Skill to find courses for
            limit (int): Maximum number of recommendations
            
        Returns:
            list: Course recommendations for the skill
        """
        # This would typically call an external API or database
        # For now, we'll generate mock course data
        
        courses = []
        search_term = skill.replace(' ', '+')
        
        # Generate mock courses from different platforms
        platforms = list(self.learning_platforms.keys())
        for i in range(min(limit, len(platforms))):
            platform = platforms[i]
            url = f"{self.learning_platforms[platform]}{search_term}"
            
            courses.append({
                'title': f"Master {skill} - Complete Course",
                'platform': platform.capitalize(),
                'url': url,
                'rating': 4.5,
                'duration': f"{4 + i} hours",
                'level': 'Beginner' if i == 0 else 'Intermediate' if i == 1 else 'Advanced'
            })
        
        return courses
    
    def comprehensive_skill_analysis(self, user_skills, job_skills):
        """
        Perform comprehensive skill analysis and provide recommendations
        
        Args:
            user_skills (list): List of user's skills
            job_skills (list): List of job requirements/skills
            
        Returns:
            dict: Comprehensive analysis with gap analysis and recommendations
        """
        # Get skill gap analysis
        gap_analysis = self.analyze_skill_gaps(user_skills, job_skills)
        
        # Get learning recommendations for missing skills
        recommendations = self.get_learning_recommendations(gap_analysis['missing_skills'])
        
        # Calculate the estimated time to close the skill gap (rough estimate)
        # Assuming average 10 hours per skill to reach basic proficiency
        estimated_hours = len(gap_analysis['missing_skills']) * 10
        
        return {
            'gap_analysis': gap_analysis,
            'recommendations': recommendations,
            'estimated_hours': estimated_hours,
            'estimated_weeks': round(estimated_hours / 10, 1),  # Assuming 10 hours of learning per week
            'priority_skills': self._get_priority_skills(gap_analysis['missing_skills'], job_skills)
        }
    
    def _get_priority_skills(self, missing_skills, job_skills, top_n=3):
        """
        Identify priority skills to learn based on job market demand
        
        Args:
            missing_skills (list): List of missing skills
            job_skills (list): List of job requirements/skills
            top_n (int): Number of priority skills to return
            
        Returns:
            list: Priority skills to learn
        """
        # This would typically use market data analysis
        # For now, we'll use a simple frequency-based approach
        
        # Just return the first N skills or all if fewer than N
        return missing_skills[:min(top_n, len(missing_skills))]


# Helper function for easy access to the analyzer
def analyze_skill_gaps(user_skills, job_skills):
    """
    Helper function to analyze skill gaps and provide recommendations
    
    Args:
        user_skills (list): List of user's skills
        job_skills (list): List of job requirements/skills
        
    Returns:
        dict: Skill gap analysis and recommendations
    """
    analyzer = SkillGapAnalyzer()
    return analyzer.comprehensive_skill_analysis(user_skills, job_skills) 
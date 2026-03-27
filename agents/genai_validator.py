"""Gen AI Output Validator - Ensures Quality and Accuracy"""

import re
from datetime import datetime

class GenAIValidator:
    """Validates Gen AI agent outputs for quality and accuracy"""
    
    def __init__(self, df):
        self.df = df
        self.validation_rules = self._init_validation_rules()
    
    def _init_validation_rules(self):
        """Initialize validation rules for Gen AI outputs"""
        return {
            'machine_id_format': r'^M\d+$',  # M1, M2, etc.
            'risk_score_range': (0, 100),
            'risk_levels': ['Critical', 'High', 'Medium', 'Low', 'Unknown'],
            'issue_types': ['vibration', 'overheating', 'lubrication', 'electrical', 'mechanical', 'hydraulic'],
            'action_types': ['temporary_fix', 'adjustment', 'part_replacement', 'inspection', 'monitoring'],
            'min_explanation_length': 20,  # characters
            'max_explanation_length': 500
        }
    
    def validate_risk_prediction(self, prediction):
        """Validate risk prediction output from AI"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['machine_id', 'risk_score', 'risk_level', 'factors']
        for field in required_fields:
            if field not in prediction:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Validate machine_id format
        if not re.match(self.validation_rules['machine_id_format'], prediction['machine_id']):
            errors.append(f"Invalid machine_id format: {prediction['machine_id']}")
        
        # Validate risk_score range
        risk_score = prediction['risk_score']
        min_score, max_score = self.validation_rules['risk_score_range']
        if not (min_score <= risk_score <= max_score):
            errors.append(f"Risk score {risk_score} out of range [{min_score}, {max_score}]")
        
        # Validate risk_level
        if prediction['risk_level'] not in self.validation_rules['risk_levels']:
            errors.append(f"Invalid risk_level: {prediction['risk_level']}")
        
        # Validate risk_level matches risk_score
        risk_level = prediction['risk_level']
        if risk_score >= 70 and risk_level != 'Critical':
            warnings.append(f"Risk score {risk_score} should be 'Critical', got '{risk_level}'")
        elif 50 <= risk_score < 70 and risk_level != 'High':
            warnings.append(f"Risk score {risk_score} should be 'High', got '{risk_level}'")
        elif 30 <= risk_score < 50 and risk_level != 'Medium':
            warnings.append(f"Risk score {risk_score} should be 'Medium', got '{risk_level}'")
        elif risk_score < 30 and risk_level not in ['Low', 'Unknown']:
            warnings.append(f"Risk score {risk_score} should be 'Low', got '{risk_level}'")
        
        # Validate factors list
        if not isinstance(prediction['factors'], list):
            errors.append("Factors must be a list")
        elif len(prediction['factors']) == 0 and risk_score > 30:
            warnings.append("High risk score but no factors provided")
        
        # Check if machine exists in data
        if prediction['machine_id'] not in self.df['machine_id'].values:
            warnings.append(f"Machine {prediction['machine_id']} not found in historical data")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'confidence': self._calculate_confidence(prediction, errors, warnings)
        }
    
    def validate_schedule_item(self, schedule_item):
        """Validate maintenance schedule item"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['machine_id', 'priority', 'scheduled_time', 'reason', 'recommended_actions']
        for field in required_fields:
            if field not in schedule_item:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Validate machine_id
        if not re.match(self.validation_rules['machine_id_format'], schedule_item['machine_id']):
            errors.append(f"Invalid machine_id format: {schedule_item['machine_id']}")
        
        # Validate scheduled_time format
        try:
            datetime.strptime(schedule_item['scheduled_time'], '%Y-%m-%d %H:%M')
        except ValueError:
            errors.append(f"Invalid scheduled_time format: {schedule_item['scheduled_time']}")
        
        # Validate reason length
        reason = schedule_item['reason']
        min_len = self.validation_rules['min_explanation_length']
        max_len = self.validation_rules['max_explanation_length']
        
        if len(reason) < min_len:
            warnings.append(f"Reason too short ({len(reason)} chars, min {min_len})")
        elif len(reason) > max_len:
            warnings.append(f"Reason too long ({len(reason)} chars, max {max_len})")
        
        # Validate recommended_actions
        if not isinstance(schedule_item['recommended_actions'], list):
            errors.append("Recommended actions must be a list")
        elif len(schedule_item['recommended_actions']) == 0:
            warnings.append("No recommended actions provided")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'confidence': self._calculate_confidence(schedule_item, errors, warnings)
        }
    
    def validate_ai_response(self, response, query):
        """Validate AI assistant response"""
        errors = []
        warnings = []
        
        # Check response is not empty
        if not response or len(response.strip()) == 0:
            errors.append("Empty response from AI")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check minimum length
        if len(response) < 20:
            warnings.append("Response too short, may not be helpful")
        
        # Check if response contains machine IDs mentioned in query
        machine_ids = re.findall(r'M\d+', query)
        for machine_id in machine_ids:
            if machine_id not in response:
                warnings.append(f"Query mentioned {machine_id} but not in response")
        
        # Check for common AI hallucination patterns
        hallucination_patterns = [
            r'I don\'t have access',
            r'I cannot see',
            r'I\'m not able to',
            r'As an AI',
            r'I apologize'
        ]
        
        for pattern in hallucination_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                warnings.append(f"Possible AI limitation detected: {pattern}")
        
        # Check if response is data-driven (contains numbers)
        if not re.search(r'\d+', response):
            warnings.append("Response lacks specific data/numbers")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'confidence': self._calculate_confidence(response, errors, warnings),
            'data_driven': bool(re.search(r'\d+', response))
        }
    
    def validate_insight(self, insight):
        """Validate generated insight"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['title', 'insight', 'action']
        for field in required_fields:
            if field not in insight:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Validate insight is actionable
        action_keywords = ['inspect', 'check', 'replace', 'schedule', 'review', 'investigate', 'monitor']
        if not any(keyword in insight['action'].lower() for keyword in action_keywords):
            warnings.append("Action may not be specific enough")
        
        # Check if insight contains data
        if not re.search(r'\d+', insight['insight']):
            warnings.append("Insight lacks specific data/metrics")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'confidence': self._calculate_confidence(insight, errors, warnings),
            'actionable': any(keyword in insight['action'].lower() for keyword in action_keywords)
        }
    
    def _calculate_confidence(self, output, errors, warnings):
        """Calculate confidence score for validation"""
        if len(errors) > 0:
            return 0
        
        # Start with 100% confidence
        confidence = 100
        
        # Reduce confidence for each warning
        confidence -= len(warnings) * 10
        
        # Ensure confidence is between 0 and 100
        return max(0, min(100, confidence))
    
    def validate_batch(self, outputs, output_type='risk_prediction'):
        """Validate multiple outputs at once"""
        results = []
        
        for output in outputs:
            if output_type == 'risk_prediction':
                result = self.validate_risk_prediction(output)
            elif output_type == 'schedule_item':
                result = self.validate_schedule_item(output)
            elif output_type == 'insight':
                result = self.validate_insight(output)
            else:
                result = {'valid': False, 'errors': [f'Unknown output type: {output_type}']}
            
            result['output'] = output
            results.append(result)
        
        # Calculate overall statistics
        valid_count = sum(1 for r in results if r['valid'])
        avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
        
        return {
            'results': results,
            'total': len(results),
            'valid': valid_count,
            'invalid': len(results) - valid_count,
            'avg_confidence': round(avg_confidence, 2),
            'pass_rate': round((valid_count / len(results)) * 100, 2) if results else 0
        }
    
    def get_validation_report(self, validation_result):
        """Generate human-readable validation report"""
        report = []
        
        if validation_result['valid']:
            report.append(f"✅ Validation PASSED (Confidence: {validation_result['confidence']}%)")
        else:
            report.append(f"❌ Validation FAILED")
        
        if validation_result['errors']:
            report.append("\n🔴 Errors:")
            for error in validation_result['errors']:
                report.append(f"  - {error}")
        
        if validation_result['warnings']:
            report.append("\n⚠️ Warnings:")
            for warning in validation_result['warnings']:
                report.append(f"  - {warning}")
        
        return "\n".join(report)

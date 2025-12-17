"""
Templates and Presets Module
Pre-configured editing templates for different content types.
"""

from typing import Dict, List, Optional
import yaml
import os
import json


class TemplateManager:
    """Manages editing templates and presets."""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)
        self.default_templates = self._create_default_templates()
        self._save_default_templates()
    
    def _create_default_templates(self) -> Dict:
        """Create default templates."""
        return {
            'tutorial': {
                'name': 'Tutorial Video',
                'description': 'Optimized for educational content',
                'settings': {
                    'remove_silences': True,
                    'min_silence_duration': 0.8,
                    'remove_fillers': True,
                    'apply_zoom': True,
                    'zoom_factor': 1.05,
                    'insert_broll': True,
                    'transition_type': 'fade',
                    'transition_duration': 0.3,
                    'color_correction': {
                        'white_balance': True,
                        'exposure': True,
                        'lut': 'corporate'
                    },
                    'subtitles': {
                        'enabled': True,
                        'style': 'modern',
                        'font_size': 24
                    }
                }
            },
            'vlog': {
                'name': 'Vlog Style',
                'description': 'Fast-paced, engaging vlog editing',
                'settings': {
                    'remove_silences': True,
                    'min_silence_duration': 0.5,
                    'remove_fillers': True,
                    'apply_zoom': True,
                    'zoom_factor': 1.1,
                    'insert_broll': True,
                    'transition_type': 'zoom',
                    'transition_duration': 0.2,
                    'color_correction': {
                        'white_balance': True,
                        'exposure': True,
                        'lut': 'vlog'
                    },
                    'subtitles': {
                        'enabled': True,
                        'style': 'bold',
                        'font_size': 28
                    }
                }
            },
            'podcast': {
                'name': 'Podcast Style',
                'description': 'Clean, professional podcast editing',
                'settings': {
                    'remove_silences': True,
                    'min_silence_duration': 1.5,
                    'remove_fillers': True,
                    'apply_zoom': False,
                    'insert_broll': False,
                    'transition_type': 'fade',
                    'transition_duration': 0.5,
                    'color_correction': {
                        'white_balance': True,
                        'exposure': True,
                        'lut': 'corporate'
                    },
                    'subtitles': {
                        'enabled': True,
                        'style': 'minimal',
                        'font_size': 22
                    }
                }
            },
            'cinematic': {
                'name': 'Cinematic Style',
                'description': 'Film-like quality with dramatic color grading',
                'settings': {
                    'remove_silences': True,
                    'min_silence_duration': 1.2,
                    'remove_fillers': True,
                    'apply_zoom': False,
                    'insert_broll': True,
                    'transition_type': 'dip_to_black',
                    'transition_duration': 0.8,
                    'color_correction': {
                        'white_balance': True,
                        'exposure': True,
                        'lut': 'cinematic'
                    },
                    'subtitles': {
                        'enabled': False
                    }
                }
            },
            'corporate': {
                'name': 'Corporate Style',
                'description': 'Professional business content',
                'settings': {
                    'remove_silences': True,
                    'min_silence_duration': 1.0,
                    'remove_fillers': True,
                    'apply_zoom': False,
                    'insert_broll': False,
                    'transition_type': 'fade',
                    'transition_duration': 0.4,
                    'color_correction': {
                        'white_balance': True,
                        'exposure': True,
                        'lut': 'corporate'
                    },
                    'subtitles': {
                        'enabled': True,
                        'style': 'minimal',
                        'font_size': 24
                    }
                }
            },
            'fast_cut': {
                'name': 'Fast Cut Style',
                'description': 'Rapid cuts, high energy',
                'settings': {
                    'remove_silences': True,
                    'min_silence_duration': 0.3,
                    'remove_fillers': True,
                    'apply_zoom': True,
                    'zoom_factor': 1.15,
                    'insert_broll': True,
                    'transition_type': 'slide',
                    'transition_duration': 0.15,
                    'color_correction': {
                        'white_balance': True,
                        'exposure': True,
                        'lut': 'vlog'
                    },
                    'subtitles': {
                        'enabled': True,
                        'style': 'bold',
                        'font_size': 30
                    }
                }
            }
        }
    
    def _save_default_templates(self):
        """Save default templates to files."""
        for template_id, template_data in self.default_templates.items():
            template_path = os.path.join(self.templates_dir, f"{template_id}.yaml")
            with open(template_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False)
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Get template by ID.
        
        Args:
            template_id: Template identifier
        
        Returns:
            Template dictionary or None
        """
        # Check defaults first
        if template_id in self.default_templates:
            return self.default_templates[template_id]
        
        # Check file system
        template_path = os.path.join(self.templates_dir, f"{template_id}.yaml")
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return yaml.safe_load(f)
        
        return None
    
    def list_templates(self) -> List[Dict]:
        """List all available templates."""
        templates = []
        
        # Add defaults
        for template_id, template_data in self.default_templates.items():
            templates.append({
                'id': template_id,
                'name': template_data['name'],
                'description': template_data['description']
            })
        
        # Add from file system
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.yaml'):
                    template_id = filename[:-5]
                    if template_id not in self.default_templates:
                        template_path = os.path.join(self.templates_dir, filename)
                        try:
                            with open(template_path, 'r') as f:
                                template_data = yaml.safe_load(f)
                                templates.append({
                                    'id': template_id,
                                    'name': template_data.get('name', template_id),
                                    'description': template_data.get('description', '')
                                })
                        except:
                            pass
        
        return templates
    
    def save_template(self, template_id: str, template_data: Dict):
        """
        Save a custom template.
        
        Args:
            template_id: Template identifier
            template_data: Template data
        """
        template_path = os.path.join(self.templates_dir, f"{template_id}.yaml")
        with open(template_path, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False)
    
    def delete_template(self, template_id: str):
        """
        Delete a custom template.
        
        Args:
            template_id: Template identifier
        """
        template_path = os.path.join(self.templates_dir, f"{template_id}.yaml")
        if os.path.exists(template_path):
            os.remove(template_path)
    
    def apply_template(self, template_id: str, base_settings: Dict) -> Dict:
        """
        Apply template settings to base settings.
        
        Args:
            template_id: Template identifier
            base_settings: Base settings dictionary
        
        Returns:
            Merged settings dictionary
        """
        template = self.get_template(template_id)
        if not template:
            return base_settings
        
        # Deep merge template settings
        merged = base_settings.copy()
        template_settings = template.get('settings', {})
        
        def deep_merge(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(merged, template_settings)
        
        return merged


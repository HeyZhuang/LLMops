import sys

def patch():
    with open('seed_medical_domain_data.py', 'r', encoding='utf-8') as f:
        old_lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(old_lines):
        if line.startswith('def build_workflow_graphs('):
            if start_idx == -1:
                start_idx = i
        if line.startswith('class Seeder:'):
            if end_idx == -1:
                end_idx = i
            
    if start_idx == -1 or end_idx == -1:
        print(f"Could not find patch points: {start_idx}, {end_idx}")
        return
        
    with open('new_data_content.py', 'r', encoding='utf-8') as f:
        new_content_lines = f.readlines()
        
    new_start_idx = -1
    for i, line in enumerate(new_content_lines):
        if line.startswith('def build_workflow_graphs('):
            new_start_idx = i
            break
            
    if new_start_idx == -1:
        print("Could not find start in new content")
        return
        
    final_lines = old_lines[:start_idx] + new_content_lines[new_start_idx:] + ['\n\n'] + old_lines[end_idx:]
    
    with open('seed_medical_domain_data.py', 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
        
    print("Patched successfully")

if __name__ == "__main__":
    patch()

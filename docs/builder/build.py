import os
import yaml
import markdown
from bs4 import BeautifulSoup
from jinja2 import Template
import shutil

def load_config():
    """Load documentation structure from config"""
    with open('docs/builder/config.yaml') as f:
        return yaml.safe_load(f)

def build_navigation(docs_dir, config):
    """Build navigation structure from config"""
    nav = []
    for section in config['sections']:
        section_files = []
        section_path = os.path.join(docs_dir, section['name'])
        
        for file_name in section['files']:
            file_path = os.path.join(section_path, file_name)
            if os.path.exists(file_path):
                with open(file_path) as f:
                    content = f.read()
                    # Extract title from first h1
                    title = content.split('\n')[0].replace('# ', '')
                    section_files.append({
                        'title': title,
                        'file': file_name,
                        'path': os.path.join(section['name'], file_name)
                    })
        
        nav.append({
            'name': section['name'],
            'title': section['title'],
            'files': section_files
        })
    
    return nav

def process_markdown(content):
    """Convert markdown to HTML with collapsible sections"""
    html = markdown.markdown(
        content,
        extensions=['toc', 'fenced_code', 'tables', 'codehilite']
    )
    
    # Convert sections to collapsible
    soup = BeautifulSoup(html, 'html.parser')
    for h2 in soup.find_all('h2'):
        section = h2.find_next_siblings()
        div = soup.new_tag('div', attrs={'class': 'content'})
        for tag in section:
            if tag.name == 'h2':
                break
            div.append(tag.extract())
        button = soup.new_tag('button', attrs={'class': 'collapsible'})
        button.string = h2.string
        h2.replace_with(button)
        button.insert_after(div)
    
    return str(soup)

def build_docs():
    """Build single page HTML documentation"""
    # Load config and template
    config = load_config()
    with open('docs/builder/template.html') as f:
        template = Template(f.read())
    
    # Build navigation
    nav = build_navigation('docs', config)
    
    # Process all markdown files
    sections = []
    for section in nav:
        section_content = []
        for file_info in section['files']:
            file_path = os.path.join('docs', file_info['path'])
            if os.path.exists(file_path):
                with open(file_path) as f:
                    content = process_markdown(f.read())
                    section_content.append({
                        'title': file_info['title'],
                        'content': content,
                        'id': file_info['path'].replace('/', '-').replace('.md', '')
                    })
        sections.append({
            'name': section['name'],
            'title': section['title'],
            'files': section_content
        })
    
    # Render template
    html = template.render(
        nav=nav,
        sections=sections
    )
    
    # Write output
    with open('karhuno_docs.html', 'w') as f:
        f.write(html)
    
    # Copy styles
    shutil.copy('docs/builder/styles.css', 'styles.css')

if __name__ == '__main__':
    build_docs()

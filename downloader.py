from pathlib import Path
import re

content = Path('content')

for md_file in content.glob('**/*.md'):
    with md_file.open() as f:
        match = re.findall(r'https:\/\/ucarecdn.com\/.*?\/', f.read())
        print(md_file, match)




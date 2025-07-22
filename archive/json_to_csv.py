import requests
import json
import csv

def main():
    url = "https://api.nearcatalog.org/projects"
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status codes
    data = response.json()

    projects = []
    for slug, proj in data.items():
        profile = proj.get('profile', {})
        image = profile.get('image', {})
        tags = profile.get('tags', {})
        lnc_raw = profile.get('lnc')
        if isinstance(lnc_raw, dict):
            lnc_score = lnc_raw.get('score')
            lnc_slug = lnc_raw.get('slug')
        else:
            lnc_score = None
            lnc_slug = None
        row = {
            'slug': proj.get('slug'),
            'name': profile.get('name'),
            'tagline': profile.get('tagline'),
            'image_url': image.get('url'),
            'tags': ', '.join(tags.values()),
            'published_date': profile.get('published_date'),
            'phase': profile.get('phase'),
            'lnc_score': lnc_score,
            'lnc_slug': lnc_slug
        }
        projects.append(row)

    if not projects:
        print("No projects found in the JSON data.")
        return

    fieldnames = list(projects[0].keys())

    with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(projects)

    print("CSV file 'output.csv' has been created successfully.")

if __name__ == "__main__":
    main() 
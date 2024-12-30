import os
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import json
from datetime import datetime

def fetch_webpage_content(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    return response.text

def download_images(img_urls):
    if not os.path.exists('img'):
        os.makedirs('img')

    for img_url in img_urls:
        try:
            response = requests.get(img_url, stream=True)
            response.raise_for_status()

            # Extract the image name from the URL
            img_name = os.path.basename(img_url)

            # Save the image to the 'img' folder
            img_path = os.path.join('img', img_name)
            with open(img_path, 'wb') as img_file:
                for chunk in response.iter_content(1024):
                    img_file.write(chunk)

            print(f"Downloaded: {img_url} -> {img_path}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to download {img_url}: {e}")

def extract_content_and_title(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')

    # Extract the title (h1 tag) and convert to title case
    title = soup.find('h1').get_text(strip=True).title() if soup.find('h1') else "Untitled"

    # Fix apostrophe capitalization issue
    title = title.replace("’L", "’l").replace("’S", "’s").replace("’T","’t")

    # Extract the content within #dm_content div
    dm_content_div = soup.find('div', id='dm_content')

    img_urls = []
    if dm_content_div:
        # Ensure all images have absolute URLs and modify their paths
        for img in dm_content_div.find_all('img'):
            if img.get('src'):
                if not img['src'].startswith('http'):
                    img['src'] = requests.compat.urljoin(base_url, img['src'])
                img_urls.append(img['src'])

                # Change the image source to WordPress upload folder
                img['src'] = f"/wp-content/uploads/2024/12/{os.path.basename(img['src'])}"

        # Convert the div's content to HTML
        content = str(dm_content_div)
    else:
        content = "<p>No content found.</p>"

    # Extract JSON-LD structured data for publication date
    date_published = ""
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if data.get('@type') == 'BlogPosting':
                date_published = data.get('datePublished', "")
                break
        except json.JSONDecodeError:
            continue

    return title, content, img_urls, date_published

def save_to_wordpress_post_xml(posts, filename_prefix="wordpress_import_posts"):
    # Generate filename with current datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.xml"

    # Create the root element
    root = ET.Element("rss", version="2.0", attrib={
        "xmlns:excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
        "xmlns:wfw": "http://wellformedweb.org/CommentAPI/",
        "xmlns:dc": "http://purl.org/dc/elements/1.1/",
        "xmlns:wp": "http://wordpress.org/export/1.2/"
    })

    # Channel element
    channel = ET.SubElement(root, "channel")

    # Add site metadata
    ET.SubElement(channel, "title").text = "Your WordPress Site Title"
    ET.SubElement(channel, "link").text = "https://example.com"
    ET.SubElement(channel, "description").text = "This is a WordPress blog post export file."
    ET.SubElement(channel, "wp:wxr_version").text = "1.2"
    ET.SubElement(channel, "wp:base_site_url").text = "https://example.com"
    ET.SubElement(channel, "wp:base_blog_url").text = "https://example.com"

    # Add posts to the channel
    for post_id, (title, content, url, date_published) in enumerate(posts, start=1):
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "pubDate").text = date_published if date_published else "Mon, 27 Dec 2024 00:00:00 +0000"
        ET.SubElement(item, "dc:creator").text = "admin"
        ET.SubElement(item, "guid", isPermaLink="false").text = url
        ET.SubElement(item, "description").text = ""
        ET.SubElement(item, "content:encoded").text = f"<![CDATA[{content}]]>"
        ET.SubElement(item, "excerpt:encoded").text = ""
        ET.SubElement(item, "wp:post_id").text = str(post_id)
        ET.SubElement(item, "wp:post_date").text = date_published.split('T')[0] if date_published else "2024-12-27 00:00:00"
        ET.SubElement(item, "wp:post_date_gmt").text = date_published.split('T')[0] if date_published else "2024-12-27 00:00:00"
        ET.SubElement(item, "wp:comment_status").text = "open"
        ET.SubElement(item, "wp:ping_status").text = "open"
        ET.SubElement(item, "wp:post_name").text = url.split('/')[-1]  # Extract the slug from the URL
        ET.SubElement(item, "wp:status").text = "publish"
        ET.SubElement(item, "wp:post_parent").text = "0"
        ET.SubElement(item, "wp:menu_order").text = "0"
        ET.SubElement(item, "wp:post_type").text = "post"
        ET.SubElement(item, "wp:post_password").text = ""
        ET.SubElement(item, "wp:is_sticky").text = "0"

    # Write to an XML file
    tree = ET.ElementTree(root)
    with open(filename, "wb") as xml_file:
        tree.write(xml_file, encoding="utf-8", xml_declaration=True)
    print(f"Content saved to {filename}")

def main():
    try:
        with open("list.txt", "r") as file:
            urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Error: list.txt file not found.")
        return

    posts = []

    for url in urls:
        print(f"Processing URL: {url}")
        html = fetch_webpage_content(url)

        if html:
            title, content, img_urls, date_published = extract_content_and_title(html, url)

            # Download images to the 'img' folder
            download_images(img_urls)

            # Append post data for XML export
            posts.append((title, content, url, date_published))

    if posts:
        save_to_wordpress_post_xml(posts)

if __name__ == "__main__":
    main()

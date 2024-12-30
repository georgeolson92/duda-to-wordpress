# duda-to-wordpress
Importing tool that converts a list of blog posts on a Duda site into an import for WordPress


1. Open terminal in repository folder
2. Add list of blog post URLs from a Duda site to 'list.txt'
3. Run 'python scraper.py'
4. Compress 'img' folder and upload images to your WordPress website under wp-content/uploads/(month)/
5. Open your WordPress site dashboard, navigate to 'Tools' and select 'Import'
6. Select 'WordPress' and upload the import file created by the program.
7. Assign user to all posts and view Posts section of Dashboard to confirm their import

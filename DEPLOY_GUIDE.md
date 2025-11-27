# How to Deploy to GitHub Pages

Since this project uses a Python backend, it cannot run fully on GitHub Pages (which only supports static sites). However, we have added a "Demo Mode" that uses mock data so the frontend can still be viewed.

## Prerequisites
- A GitHub account.
- Git installed on your computer.

## Steps

1.  **Initialize Git (if not already done)**
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    ```

2.  **Create a Repository on GitHub**
    - Go to [GitHub.com](https://github.com) and create a new repository.
    - Name it `bjtu-classroom-query` (or whatever you prefer).
    - Do **not** initialize with README/gitignore (you already have them).

3.  **Push to GitHub**
    Replace `YOUR_USERNAME` with your actual GitHub username:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/bjtu-classroom-query.git
    git branch -M main
    git push -u origin main
    ```

4.  **Configure GitHub Pages**
    - Go to your repository settings on GitHub.
    - Click on **Pages** in the left sidebar.
    - Under **Build and deployment** > **Source**, select **Deploy from a branch**.
    - Under **Branch**, select `main` and then select the `/static` folder (if available) or `/` (root).
        - *Note*: Since your `index.html` is in `static/`, you might need to configure Pages to serve from `root` and then access it via `https://yourname.github.io/repo/static/` OR move the static files to the root.
        - **Recommended**: To make it easier, you can move the contents of `static/` to the root directory for the deployment branch, or just access the URL with `/static` appended.

## Accessing the Site
Once deployed, your site will be available at:
`https://YOUR_USERNAME.github.io/bjtu-classroom-query/static/`

(If you access it, it will show the mock data because the Python backend is not running).

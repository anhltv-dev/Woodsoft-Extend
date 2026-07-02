import os
import sys
import webview

def main():
    # Resolve the path to the HTML file
    dir_path = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(dir_path, "woodsoft tool packing list.html")
    
    # Enable file downloads in webview
    webview.settings['ALLOW_DOWNLOADS'] = True
    
    # Check if file exists
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found")
        sys.exit(1)
        
    # Open window maximized
    webview.create_window(
        title='Woodsoft Packing List Tool',
        url=html_path,
        maximized=True,
        resizable=True
    )
    webview.start()

if __name__ == "__main__":
    main()

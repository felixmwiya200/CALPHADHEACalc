from PIL import Image
import sys

def remove_background(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    
    # Do a flood fill from the top-left corner
    # to make the background transparent
    # PIL's floodfill doesn't work on RGBA to change alpha easily, 
    # so we can use a trick: flood fill with a unique color, then replace it.
    
    # Convert to RGB to use ImageDraw.floodfill or use Image's floodfill?
    # Better yet, since we have numpy:
    import numpy as np
    
    data = np.array(img)
    bg_color = data[0, 0].copy()
    
    # tolerance for color distance
    tolerance = 20
    
    # boolean mask of background
    # using cityblock distance or euclidean
    diff = np.abs(data[:,:,:3].astype(int) - bg_color[:3].astype(int))
    mask = np.sum(diff, axis=2) < (tolerance * 3)
    
    # this will make ALL pixels matching background transparent.
    # to avoid making white parts inside the icon transparent, we should ideally do a flood fill.
    # Let's use skimage if available, or just a simple BFS in python.
    # Actually, a simple BFS for flood fill in Python is fast enough for small images.
    
    height, width = data.shape[:2]
    
    # Queue for BFS
    from collections import deque
    q = deque([(0,0), (0, width-1), (height-1, 0), (height-1, width-1)])
    
    visited = np.zeros((height, width), dtype=bool)
    for r, c in q:
        visited[r, c] = True
        
    while q:
        r, c = q.popleft()
        
        # If this pixel matches background, make it transparent and add neighbors
        if mask[r, c]:
            data[r, c, 3] = 0 # set alpha to 0
            
            # Add neighbors
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width and not visited[nr, nc]:
                    visited[nr, nc] = True
                    if mask[nr, nc]:
                        q.append((nr, nc))

    img2 = Image.fromarray(data)
    
    # Resize and save as ICO
    img2.save(output_path, format="ICO", sizes=[(256, 256)])
    img_png_path = output_path.replace(".ico", ".png")
    img2.save(img_png_path, format="PNG")
    print("Done")

remove_background(r'C:\Users\Dell\.gemini\antigravity\brain\40cc016d-e387-4b8a-a390-bb00125f86c4\material_fitter_icon_1790788335700.jpg', r'C:\Users\Dell\Documents\Material design\app_icon_transparent.ico')

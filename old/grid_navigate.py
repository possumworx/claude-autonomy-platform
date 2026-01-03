#!/usr/bin/env python3
"""
Grid Navigation - Amy's Revolutionary Computer Control Concept

Hierarchical screen subdivision for precise clicking without element detection.
Uses scrot for screenshots, PIL for grid overlay, xdotool for clicking.

Usage:
    grid_navigate.py screenshot  # Take initial screenshot with 3x3 grid
    grid_navigate.py 5           # Subdivide sector 5
    grid_navigate.py 2           # Subdivide subsector 2  
    grid_navigate.py click       # Click center of final selection
"""

import sys
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import json
import tempfile

class GridNavigator:
    def __init__(self):
        self.state_file = "/tmp/grid_nav_state.json"
        self.temp_dir = "/tmp/grid_nav"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize or load state
        self.state = self.load_state()
        
    def load_state(self):
        """Load current navigation state"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "level": 0,
            "x": 0, "y": 0, "width": 0, "height": 0,
            "path": [],
            "screenshot": None
        }
    
    def save_state(self):
        """Save current navigation state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def take_screenshot(self):
        """Take full screen screenshot"""
        screenshot_path = os.path.join(self.temp_dir, "current.png")
        
        # Use scrot to capture screen
        result = subprocess.run(['scrot', screenshot_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Screenshot failed: {result.stderr}")
            return None
            
        # Get screen dimensions from the image
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Initialize state for full screen
        self.state = {
            "level": 0,
            "x": 0, "y": 0, 
            "width": width, "height": height,
            "path": [],
            "screenshot": screenshot_path
        }
        self.save_state()
        
        # Create initial grid overlay
        self.create_grid_overlay()
        return screenshot_path
    
    def create_grid_overlay(self):
        """Create 3x3 grid overlay on current region"""
        if not self.state["screenshot"]:
            print("No screenshot available")
            return
            
        # Load base screenshot
        img = Image.open(self.state["screenshot"])
        draw = ImageDraw.Draw(img)
        
        # Current region bounds
        x, y = self.state["x"], self.state["y"]
        w, h = self.state["width"], self.state["height"]
        
        # Calculate grid cell size
        cell_w = w // 3
        cell_h = h // 3
        
        # Draw grid lines
        line_color = (255, 0, 0)  # Red lines
        line_width = 3
        
        # Vertical lines
        for i in range(1, 3):
            line_x = x + i * cell_w
            draw.line([(line_x, y), (line_x, y + h)], fill=line_color, width=line_width)
        
        # Horizontal lines  
        for i in range(1, 3):
            line_y = y + i * cell_h
            draw.line([(x, line_y), (x + w, line_y)], fill=line_color, width=line_width)
        
        # Draw sector numbers (1-9)
        try:
            # Try to load a font, fall back to default if not available
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        sector = 1
        for row in range(3):
            for col in range(3):
                sector_x = x + col * cell_w + cell_w // 2
                sector_y = y + row * cell_h + cell_h // 2
                
                # Draw white background circle for number
                bbox = draw.textbbox((0, 0), str(sector), font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
                
                circle_r = max(text_w, text_h) // 2 + 10
                draw.ellipse([
                    sector_x - circle_r, sector_y - circle_r,
                    sector_x + circle_r, sector_y + circle_r
                ], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
                
                # Draw sector number
                draw.text((sector_x - text_w//2, sector_y - text_h//2), 
                         str(sector), fill=(0, 0, 0), font=font)
                sector += 1
        
        # Save grid overlay image
        grid_path = os.path.join(self.temp_dir, f"grid_level_{self.state['level']}.png")
        img.save(grid_path)
        
        # Crop to current region for cleaner display
        if self.state["level"] > 0:
            region = img.crop((x, y, x + w, y + h))
            crop_path = os.path.join(self.temp_dir, f"region_level_{self.state['level']}.png")
            region.save(crop_path)
            print(f"Grid overlay saved: {crop_path}")
        else:
            print(f"Full screen grid overlay saved: {grid_path}")
        
        return grid_path
    
    def subdivide(self, sector):
        """Subdivide into selected sector (1-9)"""
        if sector < 1 or sector > 9:
            print("Sector must be 1-9")
            return
            
        # Calculate which row/col the sector is in
        sector_idx = sector - 1
        row = sector_idx // 3
        col = sector_idx % 3
        
        # Current region bounds
        x, y = self.state["x"], self.state["y"]
        w, h = self.state["width"], self.state["height"]
        
        # Calculate new bounds
        cell_w = w // 3
        cell_h = h // 3
        
        new_x = x + col * cell_w
        new_y = y + row * cell_h
        new_w = cell_w
        new_h = cell_h
        
        # Update state
        self.state["level"] += 1
        self.state["x"] = new_x
        self.state["y"] = new_y
        self.state["width"] = new_w
        self.state["height"] = new_h
        self.state["path"].append(sector)
        
        self.save_state()
        
        # Create new grid overlay
        self.create_grid_overlay()
        
        print(f"Subdivided to sector {sector} (level {self.state['level']})")
        print(f"Path: {' -> '.join(map(str, self.state['path']))}")
        print(f"Region: {new_w}x{new_h} at ({new_x}, {new_y})")
    
    def click(self):
        """Click at center of current selection"""
        if self.state["level"] == 0:
            print("No subdivision yet - take screenshot first")
            return
            
        # Calculate center of current region
        center_x = self.state["x"] + self.state["width"] // 2
        center_y = self.state["y"] + self.state["height"] // 2
        
        print(f"Clicking at ({center_x}, {center_y})")
        print(f"Path taken: {' -> '.join(map(str, self.state['path']))}")
        
        # Use xdotool to click
        result = subprocess.run(['xdotool', 'mousemove', str(center_x), str(center_y)], 
                              capture_output=True)
        if result.returncode == 0:
            subprocess.run(['xdotool', 'click', '1'])  # Left click
            print("✅ Click executed!")
        else:
            print(f"❌ Click failed: {result.stderr}")
    
    def reset(self):
        """Reset navigation state"""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        print("Navigation state reset")
    
    def status(self):
        """Show current navigation status"""
        if self.state["level"] == 0:
            print("Ready for initial screenshot")
        else:
            print(f"Level: {self.state['level']}")
            print(f"Path: {' -> '.join(map(str, self.state['path']))}")
            print(f"Region: {self.state['width']}x{self.state['height']} at ({self.state['x']}, {self.state['y']})")
            center_x = self.state["x"] + self.state["width"] // 2
            center_y = self.state["y"] + self.state["height"] // 2
            print(f"Would click at: ({center_x}, {center_y})")

def main():
    nav = GridNavigator()
    
    if len(sys.argv) < 2:
        print(__doc__)
        nav.status()
        return
    
    command = sys.argv[1].lower()
    
    if command == "screenshot":
        result = nav.take_screenshot()
        if result:
            print(f"Screenshot taken: {result}")
            print("Select sector 1-9 for subdivision")
            
    elif command == "click":
        nav.click()
        
    elif command == "reset":
        nav.reset()
        
    elif command == "status":
        nav.status()
        
    elif command.isdigit():
        sector = int(command)
        nav.subdivide(sector)
        
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
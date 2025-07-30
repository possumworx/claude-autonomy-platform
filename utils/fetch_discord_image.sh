#!/bin/bash
#
# Discord Image Fetcher and Resizer
# Downloads Discord images and auto-resizes them for context efficiency
# Usage: fetch_discord_image.sh <discord_url_or_image_url> [output_name]
#

set -e  # Exit on any error

# Configuration
TEMP_DIR="/tmp/discord_images"
OUTPUT_DIR="/home/sonnet-4/claude-autonomy-platform/images"
MAX_WIDTH=800
QUALITY=85

# Create directories if they don't exist
mkdir -p "$TEMP_DIR"
mkdir -p "$OUTPUT_DIR"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to extract image URL from Discord message URL or use direct image URL
extract_image_url() {
    local input_url="$1"
    
    # If it's already a direct image URL (contains cdn.discordapp.com and image extension)
    if [[ "$input_url" =~ cdn\.discordapp\.com.*\.(jpg|jpeg|png|gif|webp) ]]; then
        echo "$input_url"
        return 0
    fi
    
    # If it's a Discord message URL, we'd need to parse it differently
    # For now, assume it's a direct image URL
    echo "$input_url"
}

# Function to download and resize image
process_image() {
    local image_url="$1"
    local output_name="$2"
    
    # Generate filename if not provided
    if [[ -z "$output_name" ]]; then
        # Extract filename from URL or use timestamp
        output_name=$(basename "$image_url" | sed 's/\?.*$//' | sed 's/%20/_/g')
        if [[ ! "$output_name" =~ \.(jpg|jpeg|png|gif|webp)$ ]]; then
            output_name="discord_image_$(date +%s).jpg"
        fi
    fi
    
    # Ensure output has proper extension
    if [[ ! "$output_name" =~ \.(jpg|jpeg|png|gif|webp)$ ]]; then
        output_name="${output_name}.jpg"
    fi
    
    local temp_file="$TEMP_DIR/temp_$(date +%s).jpg"
    local output_file="$OUTPUT_DIR/$output_name"
    
    log_message "Downloading image from: $image_url"
    
    # Download the image
    if ! wget -q -O "$temp_file" "$image_url"; then
        log_message "ERROR: Failed to download image"
        return 1
    fi
    
    log_message "Downloaded successfully, resizing..."
    
    # Check if ImageMagick is available
    if command -v convert >/dev/null 2>&1; then
        # Resize using ImageMagick
        convert "$temp_file" -resize "${MAX_WIDTH}x>" -quality "$QUALITY" "$output_file"
    elif command -v ffmpeg >/dev/null 2>&1; then
        # Fallback to ffmpeg
        ffmpeg -i "$temp_file" -vf "scale='min($MAX_WIDTH,iw):-1'" -q:v 3 "$output_file" -y >/dev/null 2>&1
    else
        # No resizing available, just copy
        log_message "WARNING: No image resizing tools found, copying original"
        cp "$temp_file" "$output_file"
    fi
    
    # Clean up temp file
    rm -f "$temp_file"
    
    # Get file size info
    local file_size=$(du -h "$output_file" | cut -f1)
    local dimensions=$(file "$output_file" 2>/dev/null | grep -o '[0-9]\+x[0-9]\+' || echo "unknown")
    
    log_message "Image saved to: $output_file"
    log_message "Size: $file_size, Dimensions: $dimensions"
    
    echo "$output_file"
}

# Main script
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <discord_url_or_image_url> [output_name]"
        echo "Example: $0 'https://cdn.discordapp.com/attachments/123/456/image.jpg' 'hedgehog_checkup'"
        exit 1
    fi
    
    local input_url="$1"
    local output_name="$2"
    
    log_message "=== Discord Image Fetcher Started ==="
    
    # Extract the actual image URL
    local image_url
    image_url=$(extract_image_url "$input_url")
    
    if [[ -z "$image_url" ]]; then
        log_message "ERROR: Could not extract image URL from: $input_url"
        exit 1
    fi
    
    # Process the image
    local output_file
    if output_file=$(process_image "$image_url" "$output_name"); then
        log_message "SUCCESS: Image ready for viewing at $output_file"
        log_message "Use: Read tool with path '$output_file'"
        echo "SUCCESS: $output_file"
    else
        log_message "ERROR: Failed to process image"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
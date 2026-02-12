# Course Materials Image Upload Feature

## Overview
Implemented a complete image upload feature for course materials in the E-Leary platform. Users (instructors/admins) can now upload images directly within the Quill rich text editor when creating or editing course materials.

## Changes Made

### 1. Backend - Image Upload Utilities (`app/utils.py`)
Added image handling functions:
- **`allowed_image_file(filename)`** - Validates image file extensions (jpg, jpeg, png, gif, webp, svg)
- **`save_upload_image(file_obj, subfolder='materials')`** - Saves uploaded images with:
  - Unique UUID-based filenames to prevent collisions
  - Automatic subfolder creation within `/uploads/materials/`
  - Returns relative URL path for use in templates

### 2. Backend - Image Upload Endpoint (`app/routes/admin.py`)
Added new route:
- **`POST /admin/materials/upload-image`** - Handles image uploads
  - Requires pemateri (instructor) or admin authentication
  - Validates file type and size
  - Returns JSON response with:
    - `success`: Boolean indicating upload status
    - `message`: Status/error message
    - `url`: Image URL path (if successful)
  - Handles errors gracefully with appropriate HTTP status codes

### 3. Frontend - Quill Editor Enhancement (`templates/admin_manage_materials.html` & `admin_edit_material.html`)

#### Quill Configuration
- Added complete toolbar with formatting options: bold, italic, underline, strike, blockquote, code block, lists, headers, links, and **images**
- Configured modules to support image insertion

#### Image Upload Handler
- Created hidden file input element for image selection
- Intercepted Quill's image toolbar button
- Implemented async image upload via `/admin/materials/upload-image` endpoint
- Automatically inserts uploaded image URL into editor at cursor position
- Shows error alerts if upload fails

#### JavaScript Features
```javascript
- Image input listener for file selection
- FormData API for multipart/form-data submission
- Async/await for non-blocking uploads
- Error handling with user feedback
- Cursor position management for image insertion
- Input reset after upload completion
```

## User Experience Flow

1. **Instructor Creates/Edits Material**
   - Opens the material creation/edit form
   - Clicks the image icon in Quill toolbar
   - Selects image from computer

2. **Image Upload Process**
   - File is sent to `/admin/materials/upload-image`
   - Backend validates and saves with UUID filename
   - Returns image URL to frontend

3. **Image Insertion**
   - Quill automatically inserts image at cursor position
   - Image is embedded in material description HTML
   - Instructor can add more text/formatting around the image

4. **Material Storage**
   - Complete HTML (with embedded image URLs) is saved to database
   - Images stored in `/uploads/materials/` subfolder
   - All images are login-protected via existing upload route

## Security Features

- **File Type Validation**: Only allows image formats (JPG, PNG, GIF, WebP, SVG)
- **Unique Filenames**: Uses UUID to prevent overwriting and path traversal attacks
- **Permission Checks**: Upload endpoint requires pemateri/admin authentication
- **File Size Limits**: Respects Flask's MAX_CONTENT_LENGTH (50MB)
- **Protected Access**: All uploads served through `/uploads/` route requiring login

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- SVG (.svg)

## Folder Structure

```
uploads/
└── materials/
    ├── [uuid-1].jpg
    ├── [uuid-2].png
    ├── [uuid-3].gif
    └── [more images...]
```

## Database

No database schema changes required. Images are embedded as URLs in the existing `CourseMaterial.description` (TEXT field) through the Quill editor's HTML output.

## Testing Checklist

- [ ] Navigate to Admin > Manage Modules > Manage Materials
- [ ] Click image icon in description editor
- [ ] Select and upload an image
- [ ] Verify image appears in editor
- [ ] Add text before/after image
- [ ] Submit the form
- [ ] Verify material saves with embedded image
- [ ] Edit the material and verify image is preserved
- [ ] Check that images are protected (require login to view)

## Browser Compatibility

- Modern browsers with Fetch API support
- Quill 1.3.7 (already in project)
- HTML5 File API

## Future Enhancements

- Image size optimization/compression
- Drag-and-drop upload support
- Image alignment options (left, center, right)
- Image resizing in editor
- Alt text management
- Image gallery preview

## License

MIT License

Copyright (c) 2026 Asda1-max

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

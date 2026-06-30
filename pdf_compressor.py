import fitz  # PyMuPDF
from PIL import Image
import io
import os

def compress_pdf(
    input_path: str,
    output_path: str,
    quality: int = 70,
    scale: float = 0.7,
    grayscale: bool = False,
    remove_metadata: bool = True,
    progress_callback = None
) -> dict:
    """
    Compresses a PDF file by downscaling and re-compressing embedded images,
    cleaning content streams, stripping metadata, and running garbage collection.
    
    Args:
        input_path: Path to the input PDF file.
        output_path: Path to the output PDF file.
        quality: JPEG compression quality (1-100).
        scale: Scaling factor for image dimensions (0.1-1.0).
        grayscale: Whether to convert images to grayscale.
        remove_metadata: Whether to strip metadata fields.
        
    Returns:
        A dictionary with compression statistics.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Get original file size
    orig_size = os.path.getsize(input_path)
    
    # Open document
    if progress_callback:
        progress_callback(10, "Lendo documento PDF...")
    doc = fitz.open(input_path)
    
    # Track statistics
    total_images = 0
    optimized_images = 0
    skipped_images = 0
    
    # Optional: Clear metadata
    if remove_metadata:
        empty_metadata = {
            "producer": "",
            "creator": "",
            "title": "",
            "author": "",
            "subject": "",
            "keywords": "",
            "creationDate": "",
            "modDate": "",
        }
        doc.set_metadata(empty_metadata)
        
    # Extract unique image XREFs
    image_xrefs = set()
    for page in doc:
        image_list = page.get_images()
        for img in image_list:
            image_xrefs.add(img[0]) # img[0] is the xref
            
    total_images = len(image_xrefs)
    
    if progress_callback:
        progress_callback(15, f"Encontradas {total_images} imagens para processar.")
        
    # Process images
    for idx, xref in enumerate(image_xrefs):
        if progress_callback:
            # We scale image progress between 15% and 85%
            pct = int(15 + (idx / total_images) * 70) if total_images > 0 else 85
            progress_callback(pct, f"Otimizando imagem {idx + 1} de {total_images}...")
        try:
            # Extract original image
            base_image = doc.extract_image(xref)
            if not base_image:
                continue
                
            image_bytes = base_image["image"]
            
            # Load image into Pillow
            img = Image.open(io.BytesIO(image_bytes))
            
            # 1. Grayscale conversion
            if grayscale:
                img = img.convert("L")
                
            # 2. Rescaling dimensions
            width, height = img.size
            if scale < 1.0:
                new_width = max(1, int(width * scale))
                new_height = max(1, int(height * scale))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
            # 3. Compress image to buffer
            img_io = io.BytesIO()
            has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
            
            if has_alpha:
                # If image is small (like a signature/logo), keep transparency
                if img.width < 200 and img.height < 200:
                    img.save(img_io, format="PNG", optimize=True)
                    new_ext = "png"
                else:
                    # Flatten to white background JPEG to save space
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    alpha = img.convert("RGBA").split()[3]
                    background.paste(img, mask=alpha)
                    background.save(img_io, format="JPEG", quality=quality, optimize=True)
                    img = background
                    new_ext = "jpeg"
            else:
                # Save as JPEG
                img_format = "JPEG"
                if grayscale:
                    # JPEG works fine for grayscale L mode
                    img.save(img_io, format="JPEG", quality=quality, optimize=True)
                else:
                    img.convert("RGB").save(img_io, format="JPEG", quality=quality, optimize=True)
                new_ext = "jpeg"
                
            new_image_bytes = img_io.getvalue()
            
            # Only update if the compressed image is actually smaller than the original
            if len(new_image_bytes) < len(image_bytes):
                # Determine PDF filters
                filter_name = "/DCTDecode" if new_ext == "jpeg" else "/FlateDecode"
                color_space = "/DeviceGray" if (grayscale or img.mode == "L") else "/DeviceRGB"
                
                # Format the object dictionary
                new_obj = (
                    f"<<\n"
                    f"  /Type /XObject\n"
                    f"  /Subtype /Image\n"
                    f"  /BitsPerComponent 8\n"
                    f"  /Width {img.width}\n"
                    f"  /Height {img.height}\n"
                    f"  /ColorSpace {color_space}\n"
                    f"  /Filter {filter_name}\n"
                    f">>"
                )
                
                doc.update_object(xref, new_obj)
                doc.update_stream(xref, new_image_bytes, compress=0)
                optimized_images += 1
            else:
                skipped_images += 1
                
        except Exception as e:
            # If any image fails, skip it and continue to keep the PDF functional
            print(f"Skipping image xref {xref} due to error: {e}")
            skipped_images += 1
            
    # Save optimized PDF using compression flags
    # garbage=4: removes unused objects, merges duplicate objects, and checks streams
    # deflate=True: compresses streams (fonts, content, etc.)
    # clean=True: sanitizes the document structure
    if progress_callback:
        progress_callback(85, "Salvando e reestruturando PDF...")
        
    doc.save(
        output_path,
        garbage=3,
        deflate=True
    )
    doc.close()
    
    if progress_callback:
        progress_callback(100, "Compactação concluída!")
    
    # Get compressed file size
    compressed_size = os.path.getsize(output_path)
    
    # Calculate savings
    bytes_saved = max(0, orig_size - compressed_size)
    percentage_saved = (bytes_saved / orig_size) * 100 if orig_size > 0 else 0
    
    return {
        "original_size": orig_size,
        "compressed_size": compressed_size,
        "bytes_saved": bytes_saved,
        "percentage_saved": percentage_saved,
        "total_images": total_images,
        "optimized_images": optimized_images,
        "skipped_images": skipped_images
    }

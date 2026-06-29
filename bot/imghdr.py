def what(file, h=None):
    if h is None:
        if hasattr(file, "read"):
            position = file.tell()
            h = file.read(32)
            file.seek(position)
        else:
            with open(file, "rb") as source:
                h = source.read(32)

    if h.startswith(b"\xff\xd8"):
        return "jpeg"
    if h.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if h.startswith(b"BM"):
        return "bmp"

    return None

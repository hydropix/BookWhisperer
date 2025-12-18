# BookWhisperer User Guide

Complete guide for using BookWhisperer to convert your EPUB and TXT books into high-quality audiobooks.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Uploading Books](#uploading-books)
3. [Managing Books](#managing-books)
4. [Formatting Chapters](#formatting-chapters)
5. [Monitoring Progress](#monitoring-progress)
6. [Troubleshooting](#troubleshooting)
7. [Tips & Best Practices](#tips--best-practices)
8. [FAQ](#faq)

---

## Getting Started

### Prerequisites

Make sure the BookWhisperer application is running:

1. All Docker containers are up: `docker-compose ps`
2. Frontend is accessible at: http://localhost:3000
3. Backend API is accessible at: http://localhost:8000

### First-Time Setup

1. Open your web browser
2. Navigate to http://localhost:3000
3. You should see the BookWhisperer homepage

---

## Uploading Books

### Supported File Formats

- **EPUB** (.epub) - Most popular eBook format
- **TXT** (.txt) - Plain text files

### Maximum File Size

- 50 MB (configurable in backend settings)

### How to Upload

#### Method 1: Drag and Drop

1. Locate your book file on your computer
2. Drag the file into the upload area on the homepage
3. The file name will appear in the upload box
4. Optionally edit the title and author
5. Click "Upload & Process"

#### Method 2: Browse and Select

1. Click the upload area
2. Browse your computer for the book file
3. Select the file
4. Optionally edit the title and author
5. Click "Upload & Process"

### What Happens After Upload

1. **Upload Complete** - File is saved to the server
2. **Parsing Starts** - The system automatically begins extracting chapters
3. **Status Updates** - You'll see the book appear in the list with "parsing" status
4. **Parsing Complete** - Status changes to "parsed" when done

**Processing Time:**
- Small books (< 100 pages): 10-30 seconds
- Medium books (100-300 pages): 30-90 seconds
- Large books (300+ pages): 1-3 minutes

---

## Managing Books

### Viewing Your Books

All uploaded books appear in the "Your Books" list on the homepage.

**Each book card shows:**
- Book title and author
- Number of chapters
- File type (EPUB/TXT)
- Current status badge
- Delete button

### Book Status Indicators

| Status | Color | Meaning |
|--------|-------|---------|
| Pending | Gray | Uploaded, waiting to be processed |
| Parsing | Blue | Extracting chapters from the book |
| Parsed | Green | Chapters extracted successfully |
| Formatting | Yellow | LLM is formatting text |
| Generating | Purple | Audio is being generated |
| Completed | Green | All processing complete |
| Failed | Red | An error occurred |

### Viewing Book Details

1. Click on any book in the list
2. You'll see:
   - Full book information
   - Chapter count
   - Status
   - List of all chapters
   - Progress tracker (if processing)

### Deleting Books

1. Click the trash icon next to a book
2. Confirm the deletion in the dialog
3. The book and all its data will be permanently removed

**Warning:** Deletion cannot be undone. All chapters and generated audio will be deleted.

---

## Formatting Chapters

### What is Formatting?

Formatting uses a Large Language Model (LLM) to:
- Clean and normalize text
- Fix grammar and punctuation
- Format dialogue properly
- Add natural pauses for narration
- Remove formatting artifacts

This prepares the text for high-quality audiobook generation.

### Formatting All Chapters

1. Navigate to a book's detail page
2. Wait for status to be "parsed"
3. Click "Format All Chapters" button
4. Confirm in the dialog
5. Monitor progress in the tracker

**When to Use:**
- After a book has been successfully parsed
- Before generating audio (recommended)
- To improve text quality for narration

### Formatting Single Chapters

1. Navigate to a book's detail page
2. Find the chapter in the list
3. Click "Format" button for that chapter
4. Monitor progress in the tracker

**When to Use:**
- Testing the formatting quality
- Re-formatting a specific chapter
- Selective processing

### Formatting Time

**Per Chapter:**
- Small chapters (< 2000 words): 10-30 seconds
- Medium chapters (2000-5000 words): 30-90 seconds
- Large chapters (5000+ words): 90-180 seconds

**Factors affecting speed:**
- LLM model used (llama2 vs mistral)
- Server hardware (CPU/GPU)
- Chapter complexity
- Current server load

---

## Monitoring Progress

### Progress Tracker

The progress tracker appears automatically when processing is active.

**Shows:**
- Active job type (parsing, formatting, generating)
- Progress percentage
- Current chunk (for multi-chunk processing)
- Errors if any occur
- Retry count

### Real-Time Updates

The tracker polls for updates every 2 seconds, showing:
- ⏱️ Pending - Job queued
- 🔄 Processing - Job running
- ✅ Completed - Job finished
- ❌ Failed - Job error

### Viewing in Flower

For detailed monitoring:
1. Open http://localhost:5555
2. View all Celery tasks
3. See detailed task history
4. Monitor worker status

---

## Troubleshooting

### Upload Issues

**Problem:** "Upload failed" error

**Solutions:**
- Check file is .epub or .txt
- Verify file size is under 50MB
- Ensure backend is running
- Check file isn't corrupted

**Problem:** Upload succeeds but parsing fails

**Solutions:**
- For EPUB: File may have non-standard structure
- For TXT: Try adding clear chapter markers (Chapter 1, Chapter 2, etc.)
- Check error message in book details

### Parsing Issues

**Problem:** No chapters detected

**For EPUB:**
- The book may not have a table of contents
- Try with a different EPUB file

**For TXT:**
- Add clear chapter markers:
  - "Chapter 1", "Chapter 2", etc.
  - "CHAPTER I", "CHAPTER II", etc.
  - "Part 1", "Part 2", etc.
- Ensure chapters are separated by blank lines

**Problem:** Too many/few chapters detected

- This can happen with complex formatting
- Manual chapter selection will be added in future

### Formatting Issues

**Problem:** Formatting fails with error

**Solutions:**
- Check Ollama service is running: `docker-compose ps`
- Verify Ollama model is pulled: `docker exec -it bookwhisperer_ollama ollama list`
- Check backend logs: `docker-compose logs backend`
- Try formatting single chapter first

**Problem:** Formatting is very slow

**Solutions:**
- Check server resource usage
- Consider using a smaller/faster model (llama2 vs mixtral)
- Reduce concurrent jobs
- Ensure GPU is available if configured

### General Issues

**Problem:** Page won't load

**Solutions:**
- Verify frontend container is running
- Check http://localhost:3000 is accessible
- Clear browser cache
- Check browser console for errors

**Problem:** Can't delete a book

**Solutions:**
- Wait for any active jobs to complete
- Refresh the page
- Check backend logs for errors

---

## Tips & Best Practices

### For Best Results

1. **Use high-quality source files**
   - Well-formatted EPUBs work best
   - For TXT, use clear chapter markers

2. **Start small**
   - Test with a short book first
   - Verify formatting quality before processing large books

3. **Monitor resources**
   - Check Flower dashboard during processing
   - Avoid uploading many books simultaneously

4. **Regular backups**
   - Export generated audio regularly
   - Keep source files backed up

### Optimizing Performance

1. **Chapter formatting**
   - Format chapters during off-peak hours
   - Process one book at a time for fastest results

2. **File preparation**
   - Clean up source files before upload
   - Remove unnecessary front/back matter
   - Ensure proper chapter structure

3. **Resource management**
   - Close unused browser tabs
   - Monitor Docker container resources
   - Restart services if they become unresponsive

### Quality Checks

1. **After parsing**
   - Verify chapter count is correct
   - Check a few chapters have proper content
   - Look for any parsing errors

2. **After formatting**
   - Read formatted text samples
   - Check dialogue formatting
   - Verify punctuation improvements

---

## FAQ

### General

**Q: What makes BookWhisperer different from other audiobook tools?**

A: BookWhisperer uses LLM technology to intelligently format text specifically for audiobook narration, improving quality and naturalness.

**Q: Can I use this with copyrighted books?**

A: Only use books you have the legal right to convert. Respect copyright laws.

**Q: Is my data private?**

A: BookWhisperer runs locally on your machine. No data is sent to external services (except local Ollama LLM).

### Technical

**Q: Which Ollama model should I use?**

A:
- **llama2** - Good balance of speed and quality (recommended)
- **mistral** - Slightly faster, similar quality
- **mixtral** - Best quality, much slower, requires more resources

**Q: Can I process multiple books simultaneously?**

A: Yes, but it will slow down individual book processing. Best to do one at a time.

**Q: How much disk space do I need?**

A:
- Ollama models: 4-26 GB depending on model
- Each book: ~10-50 MB (original + chapters + audio)
- Recommended: 50GB+ free space

**Q: Can I run this on a Raspberry Pi?**

A: Not recommended. LLM processing requires significant CPU/RAM. Minimum 8GB RAM, modern CPU.

### Features

**Q: Can I choose different voices?**

A: Voice selection will be added in future updates (Phase 4+).

**Q: Can I edit the text before generating audio?**

A: Currently no. This feature is planned for future releases.

**Q: Can I merge all audio files into one?**

A: ZIP download of all files is available. Single file merge planned for future.

**Q: Can I customize the formatting style?**

A: Currently no. Custom prompts/styles planned for future releases.

### Troubleshooting

**Q: Why is formatting taking so long?**

A: LLM processing is CPU-intensive. Large chapters on slower hardware can take several minutes.

**Q: What if I close my browser during processing?**

A: Processing continues in the background. Refresh the page to see current progress.

**Q: Can I cancel a running job?**

A: Job cancellation is not currently supported but is planned for a future release.

**Q: Why does my book show "failed" status?**

A: Check the error message in the book details. Common causes:
- Corrupted file
- Unsupported format variation
- Service unavailable
- Out of disk space

---

## Getting Help

### Resources

- **API Documentation:** See `docs/API_DOCUMENTATION.md`
- **Deployment Guide:** See `docs/DEPLOYMENT.md`
- **README:** See project README.md

### Support Channels

- **GitHub Issues:** Report bugs and request features
- **Logs:** Check Docker logs for detailed errors:
  ```bash
  docker-compose logs backend
  docker-compose logs celery_worker
  docker-compose logs ollama
  ```

### Reporting Issues

When reporting issues, please include:
1. Steps to reproduce
2. Error messages
3. Book file type and size
4. System specs (RAM, CPU, OS)
5. Docker logs if available

---

## What's Next?

### Coming Soon (Phase 4+)

- ✨ Audio generation with TTS
- 🎙️ Multiple voice options
- ⬇️ Bulk download as ZIP
- 📝 Text editing before processing
- ⏸️ Job pause/resume
- 🔍 Search and filter books
- 👥 Multi-user support with authentication

### Stay Updated

Check the project README and CHANGELOG for latest updates and new features.

---

**Happy reading (and listening)! 📚🎧**

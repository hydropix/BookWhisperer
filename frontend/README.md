# BookWhisperer Frontend

React + TypeScript frontend for the BookWhisperer audiobook generation platform.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **TanStack Query** - Server state management
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Features

### 📚 Book Management
- Drag-and-drop file upload (EPUB/TXT)
- Book listing with pagination
- Book details view with metadata
- Delete books

### 📖 Chapter Management
- View all chapters in a book
- Individual chapter formatting
- Batch chapter formatting
- Chapter status tracking

### 📊 Progress Tracking
- Real-time job status updates
- Progress bars with percentage
- Automatic polling for active jobs
- Error handling and retry information

### 🎨 UI/UX
- Dark mode support
- Responsive design
- Loading states
- Error handling
- Toast-like notifications
- Smooth transitions and animations

## Project Structure

```
frontend/
├── src/
│   ├── api/               # API client and endpoints
│   │   ├── client.ts      # Axios instance with interceptors
│   │   ├── books.ts       # Book API endpoints
│   │   ├── chapters.ts    # Chapter API endpoints
│   │   ├── jobs.ts        # Job status API
│   │   ├── health.ts      # Health check API
│   │   └── index.ts       # Exports
│   ├── components/        # React components
│   │   ├── BookUpload.tsx       # File upload with drag-drop
│   │   ├── BookList.tsx         # Book listing table
│   │   ├── BookDetails.tsx      # Book info display
│   │   ├── ChapterList.tsx      # Chapter listing
│   │   └── ProgressTracker.tsx  # Job progress tracking
│   ├── hooks/             # Custom React hooks
│   │   ├── useBooks.ts    # Book CRUD operations
│   │   ├── useChapters.ts # Chapter operations
│   │   └── usePolling.ts  # Auto-refresh hook
│   ├── pages/             # Route pages
│   │   ├── Home.tsx       # Home page (upload + list)
│   │   └── BookPage.tsx   # Book details page
│   ├── types/             # TypeScript types
│   │   └── index.ts       # All type definitions
│   ├── App.tsx            # Root component with routing
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
├── public/                # Static assets
├── index.html            # HTML template
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── vite.config.ts        # Vite config
├── tailwind.config.js    # Tailwind config
├── Dockerfile            # Production build
└── nginx.conf            # Nginx config for production
```

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Start development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## API Integration

The frontend communicates with the backend API at `http://localhost:8000/api/v1` by default.

### API Client Configuration

Configure the API URL in `.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Endpoints Used

#### Books
- `GET /books` - List all books
- `GET /books/{id}` - Get book details
- `POST /books/upload` - Upload new book
- `DELETE /books/{id}` - Delete book
- `POST /books/{id}/chapters/format` - Format all chapters

#### Chapters
- `GET /books/{id}/chapters` - List chapters
- `GET /chapters/{id}` - Get chapter details
- `POST /chapters/{id}/format` - Format single chapter

#### Jobs
- `GET /jobs/{id}` - Get job status
- `GET /books/{id}/jobs` - Get all jobs for book

#### Health
- `GET /health` - API health check
- `GET /health/all` - All services health

## State Management

The app uses **TanStack Query** (React Query) for server state:

- Automatic caching
- Background refetching
- Optimistic updates
- Query invalidation
- Polling for active jobs

### Example Usage

```typescript
// Fetch books with automatic caching
const { data, isLoading } = useBooks(page, pageSize)

// Upload with automatic cache invalidation
const uploadMutation = useUploadBook()
await uploadMutation.mutateAsync({ file, title, author })

// Auto-polling for updates
usePolling({
  enabled: isProcessing,
  interval: 2000,
  queryKey: ['book', bookId],
})
```

## Components

### BookUpload
Drag-and-drop file upload with preview and metadata input.

Features:
- Drag-and-drop zone
- File type validation (EPUB/TXT)
- Auto-extract title from filename
- Manual title/author input
- Upload progress indicator

### BookList
Paginated list of books with status indicators.

Features:
- Responsive table/card view
- Status badges with colors
- Click to view details
- Delete with confirmation
- Pagination controls

### BookDetails
Detailed view of a single book.

Features:
- Book metadata display
- Chapter count and stats
- Format all chapters button
- Error messages
- Status tracking

### ChapterList
List of chapters with formatting controls.

Features:
- Chapter number and title
- Word/character counts
- Status indicators
- Individual format buttons
- Real-time status updates

### ProgressTracker
Real-time job progress monitoring.

Features:
- Progress bars with percentage
- Job type labels
- Chunk progress for LLM formatting
- Error display
- Retry counter
- Auto-polling while active

## Styling

### TailwindCSS

The app uses TailwindCSS for styling with:
- Dark mode support
- Custom color palette (primary blue theme)
- Responsive breakpoints
- Utility classes

### Custom Theme

Primary color palette:
```js
primary: {
  50: '#f0f9ff',
  500: '#0ea5e9',  // Main brand color
  600: '#0284c7',
  900: '#0c4a6e',
}
```

### Dark Mode

Dark mode is automatically detected from system preferences:
- Uses `dark:` variant classes
- Consistent contrast ratios
- Proper color inversions

## Production Build

### Docker Build

```bash
docker build -t bookwhisperer-frontend .
docker run -p 3000:80 bookwhisperer-frontend
```

### Manual Build

```bash
npm run build
```

Built files will be in `dist/` directory.

### Nginx Configuration

The production build uses Nginx with:
- SPA routing (all routes → index.html)
- API proxy to backend
- Static asset caching
- Gzip compression

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |

## Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)

## Performance

- Code splitting by route
- Lazy loading of components
- Optimized images
- Cached API responses
- Minimal bundle size (~200KB gzipped)

## Accessibility

- Semantic HTML
- ARIA labels where needed
- Keyboard navigation
- Focus management
- Screen reader friendly

## Future Enhancements

- [ ] Audio player component
- [ ] Download book as ZIP
- [ ] Streaming audio playback
- [ ] Chapter preview/editing
- [ ] Voice selection for TTS
- [ ] Batch operations
- [ ] Search and filtering
- [ ] Sorting options
- [ ] User preferences
- [ ] Themes customization

## Troubleshooting

### API Connection Issues

If you see connection errors:
1. Check backend is running at `http://localhost:8000`
2. Verify CORS is enabled on backend
3. Check `.env` has correct `VITE_API_URL`

### Build Errors

If build fails:
1. Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf .vite`
3. Check Node version: `node --version` (should be 20+)

### Styling Issues

If Tailwind classes don't work:
1. Check `tailwind.config.js` content paths
2. Verify PostCSS is installed
3. Restart dev server

## Contributing

1. Follow the TypeScript strict mode
2. Use functional components with hooks
3. Keep components small and focused
4. Add proper TypeScript types
5. Test in both light and dark modes
6. Ensure responsive design

## License

MIT

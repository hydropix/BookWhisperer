import BookUpload from '../components/BookUpload'
import BookList from '../components/BookList'

export default function Home() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome to BookWhisperer
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Transform your EPUB and TXT files into high-quality audiobooks
        </p>
      </div>

      <BookUpload />
      <BookList />
    </div>
  )
}

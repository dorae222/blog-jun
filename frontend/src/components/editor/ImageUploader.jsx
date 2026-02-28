import { useRef } from 'react'
import toast from 'react-hot-toast'
import { uploadImage } from '../../api/posts'

export default function ImageUploader({ onInsert }) {
  const inputRef = useRef(null)

  const handleUpload = async (file) => {
    if (!file || !file.type.startsWith('image/')) {
      toast.error('Please select an image file')
      return
    }

    const formData = new FormData()
    formData.append('image', file)

    try {
      const { data } = await uploadImage(formData)
      onInsert(`![${file.name}](${data.image})`)
      toast.success('Image uploaded!')
    } catch {
      toast.error('Upload failed')
    }
  }

  return (
    <>
      <button
        onClick={() => inputRef.current?.click()}
        className="text-sm px-3 py-1 rounded border hover:bg-gray-50 dark:hover:bg-gray-800"
        style={{ borderColor: 'var(--border)' }}
      >
        Upload Image
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={e => handleUpload(e.target.files[0])}
      />
    </>
  )
}

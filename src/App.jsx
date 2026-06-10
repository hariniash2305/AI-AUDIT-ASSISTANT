import { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post(
      "http://127.0.0.1:8000/upload",
      formData
    );

    setMessage(response.data.message);
  };

  return (
    <div>
      <h1>AI Audit Assistant</h1>

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button onClick={handleUpload}>
        Upload
      </button>

      <p>{message}</p>
    </div>
  );
}

export default App; 

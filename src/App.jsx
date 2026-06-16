import { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/upload",
        formData
      );

      setData(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ padding: "30px" }}>
      <h1>AI Audit Assistant</h1>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button
        onClick={handleUpload}
        style={{ marginLeft: "10px" }}
      >
        Upload
      </button>
      {data && (
  <div
    style={{
      marginTop: "30px",
      border: "1px solid #ddd",
      borderRadius: "10px",
      padding: "20px",
      width: "350px",
      boxShadow: "0 2px 5px rgba(0,0,0,0.1)"
    }}
  >
    <h2>{data.document_type.toUpperCase()}</h2>

    {data.document_type === "invoice" ? (
      <>
        <p>
          <strong>Invoice Number:</strong>
          {data.data.invoice_number}
        </p>

        <p>
          <strong>Vendor:</strong>
          {data.data.vendor}
        </p>

        <p>
          <strong>Amount:</strong>
          ₹{data.data.amount}
        </p>

        <p>
          <strong>Date:</strong>
          {data.data.date}
        </p>
      </>
    ) : (
      <>
        <p>
          <strong>PO Number:</strong>
          {data.data.po_number}
        </p>

        <p>
          <strong>Vendor:</strong>
          {data.data.vendor}
        </p>

        <p>
          <strong>Amount:</strong>
          ₹{data.data.amount}
        </p>

        <p>
          <strong>Date:</strong>
          {data.data.date}
        </p>
      </>
    )}
  </div>
)}
      
    </div>
  );
}

export default App;

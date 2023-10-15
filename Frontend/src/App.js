import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [questions, setQuestions] = useState({});
  const [loading, setLoading] = useState(false);

  const onFileChange = (e) => {
    setUploadedFiles(e.target.files);
  };

  const onFormSubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    for (const file of uploadedFiles) {
      formData.append("resumes", file);
    }

    setLoading(true);

    try {
      const response = await axios.post("http://localhost:5000/generate_questions", formData);
      setQuestions(response.data);
    } catch (error) {
      console.error("Error uploading files:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Resume Reader and Interview Questions Creator</h1>
      <p>This can be used for mock interviews and practice but also by companies trying to hire.</p>

      <form onSubmit={onFormSubmit}>
        <label>
          Upload resumes:
          <input type="file" name="resumes" directory="" webkitdirectory="" onChange={onFileChange} multiple />
        </label>
        <button type="submit">Generate Questions</button>
      </form>

      {loading && <p style={{ color: 'gray' }}>Generating...</p>}

      <div className="questions-section">
        {Object.entries(questions).map(([filename, questionsList]) => (
          <div key={filename}>
            <h2>{filename.split('/').pop()}</h2>
            <ul>
              {questionsList.map((question, index) => (
                <li key={index}>{question}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;

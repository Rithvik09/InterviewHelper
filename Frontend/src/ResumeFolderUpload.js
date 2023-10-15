import React, { useState } from 'react';
import axios from 'axios';

function ResumeFolderUpload() {
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleFolderChange = (e) => {
    setUploadedFiles(e.target.files);
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    for (let i = 0; i < uploadedFiles.length; i++) {
      formData.append("resumes", uploadedFiles[i]);
    }

    try {
      const response = await axios.post("http://localhost:5000/generate_questions", formData);
      console.log(response.data);
    } catch (error) {
      console.error("Error uploading resumes:", error);
    }
  };

  return (
    <div>
      <input type="file" directory="" webkitdirectory="" onChange={handleFolderChange} />
      <button onClick={handleSubmit}>Upload Resumes and Generate Questions</button>
    </div>
  );
}

export default ResumeFolderUpload;

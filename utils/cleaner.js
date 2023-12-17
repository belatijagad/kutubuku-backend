const fs = require('fs');

// Replace 'books.json' with the path to your JSON file
const jsonFilePath = './utils/output/novels.json';

// Use readFile to read the file content
fs.readFile(jsonFilePath, 'utf8', (err, jsonString) => {
  if (err) {
    console.error('Error reading the JSON file:', err);
    return;
  }
  try {
    // Parse the JSON string into a JavaScript object
    const books = JSON.parse(jsonString);
    
    // Now `books` is an array of book objects
    // Here you can process your books array
    books.forEach(book => {
      book.synopsis = removeDuplicateSentences(book.synopsis);
    });
    
    // For demonstration: logging the first book's title
    console.log('First book title:', books[0].title);
    fs.writeFileSync('./utils/output/novels_cleaned.json', JSON.stringify(books));

  } catch (err) {
    console.error('Error parsing JSON string:', err);
  }
});

// The removeDuplicateSentences function as previously described
function removeDuplicateSentences(synopsis) {
  const sentences = synopsis.split('|');
  const uniqueSentencesSet = new Set(sentences);
  return Array.from(uniqueSentencesSet).join('\n').trim();
}


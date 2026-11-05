import React from 'react';
import { createRoot } from 'react-dom/client';
import { Tweet } from 'react-tweet';
const id = new URLSearchParams(location.search).get('id');
createRoot(document.getElementById('root')).render(<div data-tweet-wrap><Tweet id={id} /></div>);

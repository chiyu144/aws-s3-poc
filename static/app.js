const host = window.location.href;
const messagesApi = async(method, formData=undefined) => {
  try {
    const apiUrl = new URL('/api/messages', host);
    const res = await fetch(apiUrl.toString(), {
      method: `${method}`,
      body: formData ? formData : undefined
    });
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn(err);
  };
};
const getMessages = async() => {
  const res = await messagesApi('GET');
  if (res.error) console.log('Error: Get Messages Failed.')
  else return res.data;
};
const postMessage = async(formData) => {
  const messageButton = document.querySelector('#button-message');
  messageButton.disabled = true;
  messageButton.textContent = '處理中…';
  const res = await messagesApi('POST', formData);
  if (res.error) console.log('Error: Post Message Failed.')
  if (res.ok) {
    const messages = await getMessages();
    const messagesContainer = document.querySelector('#container-messages');
    while (messagesContainer.firstChild) {
      messagesContainer.removeChild(messagesContainer.firstChild);
    };
    render(messages, true);
    messageButton.textContent = '送出留言';
    messageButton.disabled = false;
    messageForm.reset();
  };
};
const render = (messages, isReRender = false) => {
  const messagesContainer = document.querySelector('#container-messages');
  messages.forEach((message, index) => {
    const image = document.createElement('img');
    image.src = message.image_url;
    image.classList.add('object-cover', 'object-center');
  
    const imageWrap = document.createElement('div');
    imageWrap.classList.add('mt-2', 'mb-1.5');
    imageWrap.appendChild(image);
  
    const content = document.createElement('div');
    content.classList.add('text-blue-500', 'text-lg', 'font-bold');
    content.textContent = message.content
  
    const messageWrap = document.createElement('div');
    messageWrap.classList.add('mx-auto', 'my-8', 'p-4', 'border', 'border-solid', 'border-zinc-300', 'rounded-md', 'md:max-w-2xl');
    messageWrap.appendChild(content);
    messageWrap.appendChild(imageWrap);
  
    messagesContainer.appendChild(messageWrap);

    if (index === messages.length - 1 && isReRender) {
      const timerId = setTimeout(() => {
        window.scroll({top: document.body.scrollHeight, behavior: 'smooth'});
        clearTimeout(timerId);
      }, 500);
    };
  });
};
document.addEventListener('DOMContentLoaded', async() => {
  const errorHint = document.querySelector('#hint-error'); 
  const messageForm = document.querySelector('#form-message');
  const backtotopLink = document.querySelector('#link-backtotop');
  const messages = await getMessages();
  if(messages.length > 0){render(messages);}

  messageForm.addEventListener('submit', async(e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const content =  formData.get('content');
    const imageFile = formData.get('image-file');
    if (content === '' || imageFile.size === 0) errorHint.classList.remove('hidden');
    else {
      !errorHint.classList.contains('hidden') && errorHint.classList.add('hidden');
      postMessage(formData);
    };
  });
  backtotopLink.addEventListener('click', (e) => {
    e.preventDefault();
    window.scroll({top: 0, behavior: 'smooth'});
  });
});
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const files = document.getElementById('kb-files').files;
    if (files.length === 0) return alert('Выберите файлы');
    
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }
    
    const statusDiv = document.getElementById('upload-status');
    statusDiv.textContent = 'Загрузка и обработка... (Это может занять время)';
    
    try {
        const response = await fetch('/api/upload_knowledge', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        statusDiv.textContent = data.message;
    } catch (err) {
        statusDiv.textContent = 'Ошибка загрузки: ' + err;
    }
});

let checkStatusInterval;

document.getElementById('task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const desc = document.getElementById('task-desc').value;
    const files = document.getElementById('task-files').files;
    
    const formData = new FormData();
    formData.append('task_description', desc);
    for (const file of files) {
        formData.append('files', file);
    }
    
    const statusDiv = document.getElementById('task-status');
    const resultsDiv = document.getElementById('results');
    
    statusDiv.textContent = 'Запуск генерации...';
    resultsDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/generate_hypotheses', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.task_id) {
            statusDiv.textContent = 'Обработка (работают агенты)...';
            checkStatusInterval = setInterval(() => checkStatus(data.task_id), 3000);
        }
    } catch (err) {
        statusDiv.textContent = 'Ошибка запуска: ' + err;
    }
});

async function checkStatus(taskId) {
    try {
        const response = await fetch('/api/result/' + taskId);
        const data = await response.json();
        
        const statusDiv = document.getElementById('task-status');
        const resultsDiv = document.getElementById('results');
        const progressContainer = document.getElementById('progress-container');
        const progressBar = document.getElementById('pipeline-progress');
        const progressText = document.getElementById('progress-text');
        
        if (data.status === 'not_found') return;
        
        progressContainer.style.display = 'block';
        if (data.stage !== undefined) {
            progressBar.value = data.stage;
            progressText.textContent = data.stage_desc || 'Обработка...';
        }
        
        if (data.status === 'completed') {
            clearInterval(checkStatusInterval);
            statusDiv.textContent = 'Готово!';
            progressBar.value = 6;
            progressText.textContent = 'Успешно завершено';
            renderResults(data.data);
        } else if (data.status === 'failed') {
            clearInterval(checkStatusInterval);
            statusDiv.textContent = 'Ошибка генерации: ' + data.error;
            progressText.textContent = 'Произошла ошибка';
        }
    } catch(err) {
        console.error(err);
    }
}

function renderResults(hypotheses) {
    const resultsDiv = document.getElementById('results');
    let html = '';
    
    if (hypotheses.length === 0) {
        html = '<p>Не удалось сгенерировать гипотезы.</p>';
    } else {
        hypotheses.forEach((hyp, idx) => {
            const title = hyp.название || (hyp.воздействие ? `${hyp.воздействие} на ${hyp.объект}` : 'Без названия');
            const desc = hyp.описание || (hyp.параметр ? `Изменение параметра: ${hyp.параметр} (${hyp.направление})` : '-');
            
            let obosnovanieHtml = '-';
            if (Array.isArray(hyp.обоснование)) {
                obosnovanieHtml = '<ul>' + hyp.обоснование.map(o => `<li><strong>${o.источник || 'Источник'}</strong> (${o.локация || ''}): ${o.тезис || ''}</li>`).join('') + '</ul>';
            } else if (typeof hyp.обоснование === 'object' && hyp.обоснование !== null) {
                let o = hyp.обоснование;
                obosnovanieHtml = '<ul>' + `<li><strong>${o.источник || 'Источник'}</strong> (${o.локация || ''}): ${o.тезис || ''}</li>` + '</ul>';
            } else if (hyp.обоснование) {
                obosnovanieHtml = hyp.обоснование;
            }
            
            let sources = hyp.источники || [];
            if (Array.isArray(hyp.обоснование)) {
                 sources = [...new Set(hyp.обоснование.map(o => o.источник).filter(Boolean))];
            } else if (typeof hyp.обоснование === 'object' && hyp.обоснование !== null && hyp.обоснование.источник) {
                 sources = [hyp.обоснование.источник];
            }
            
            let scoresHtml = '';
            if (hyp.оценки) {
                scoresHtml = '<ul>' + Object.entries(hyp.оценки).map(([k, v]) => `<li>${k}: ${v.значение || v}</li>`).join('') + '</ul>';
            }

            html += `
                <div class="hypothesis">
                    <h3>${idx + 1}. ${title}</h3>
                    <p><strong>Описание:</strong> ${desc}</p>
                    <p><strong>Механизм:</strong> ${hyp.механизм || '-'}</p>
                    <p><strong>Обоснование:</strong> ${obosnovanieHtml}</p>
                    <p><strong>Метрики:</strong> ${scoresHtml || '-'}</p>
                    <p><strong>Источники:</strong> ${sources.join(', ') || '-'}</p>
                    <p><strong>Оценка директора:</strong> ${hyp.итоговая_оценка_от_директора || '-'} (Балл: ${hyp.total_score || '-'})</p>
                </div>
            `;
        });
    }
    resultsDiv.innerHTML = html;
    
    const downloadBtn = document.getElementById('download-md-btn');
    if (hypotheses.length > 0) {
        downloadBtn.style.display = 'inline-block';
        window.currentHypotheses = hypotheses;
    } else {
        downloadBtn.style.display = 'none';
        window.currentHypotheses = [];
    }
}

document.getElementById('download-md-btn').addEventListener('click', () => {
    if (!window.currentHypotheses || window.currentHypotheses.length === 0) return;
    
    let md = '# Результаты генерации гипотез\n\n';
    
    window.currentHypotheses.forEach((hyp, idx) => {
        const title = hyp.название || (hyp.воздействие ? `${hyp.воздействие} на ${hyp.объект}` : 'Без названия');
        const desc = hyp.описание || (hyp.параметр ? `Изменение параметра: ${hyp.параметр} (${hyp.направление})` : '-');
        
        md += `## ${idx + 1}. ${title}\n\n`;
        md += `**Описание:** ${desc}\n\n`;
        md += `**Механизм:** ${hyp.механизм || '-'}\n\n`;
        
        md += `**Обоснование:**\n`;
        if (Array.isArray(hyp.обоснование)) {
            hyp.обоснование.forEach(o => {
                md += `- **${o.источник || 'Источник'}** (${o.локация || ''}): ${o.тезис || ''}\n`;
            });
        } else if (typeof hyp.обоснование === 'object' && hyp.обоснование !== null) {
            let o = hyp.обоснование;
            md += `- **${o.источник || 'Источник'}** (${o.локация || ''}): ${o.тезис || ''}\n`;
        } else {
            md += `${hyp.обоснование || '-'}\n`;
        }
        md += '\n';
        
        md += `**Метрики:**\n`;
        if (hyp.оценки) {
            Object.entries(hyp.оценки).forEach(([k, v]) => {
                md += `- ${k}: ${v.значение || v}\n`;
            });
        } else {
            md += `-\n`;
        }
        md += '\n';
        
        let sources = hyp.источники || [];
        if (Array.isArray(hyp.обоснование)) {
             sources = [...new Set(hyp.обоснование.map(o => o.источник).filter(Boolean))];
        } else if (typeof hyp.обоснование === 'object' && hyp.обоснование !== null && hyp.обоснование.источник) {
             sources = [hyp.обоснование.источник];
        }
        md += `**Источники:** ${sources.join(', ') || '-'}\n\n`;
        md += `**Оценка директора:** ${hyp.итоговая_оценка_от_директора || '-'} (Балл: ${hyp.total_score || '-'})\n\n`;
        md += '---\n\n';
    });
    
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hypotheses_results_${new Date().getTime()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

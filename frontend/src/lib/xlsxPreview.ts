import { read, utils } from 'xlsx';

export async function parseHeadersAndRows(file: File, maxRows = 5): Promise<{ headers: string[]; rows: Array<Record<string, any>>; }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = e.target?.result;
        if (!data) {
          reject(new Error('File data is empty.'));
          return;
        }

        const workbook = read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];

        // Get headers from the first row
        const headerRow = utils.sheet_to_json(worksheet, { header: 1 })[0] as string[];
        const headers = headerRow || [];

        // Get data rows, using the first row as headers for object keys
        const allRows: Array<Record<string, any>> = utils.sheet_to_json(worksheet, { raw: false });

        // Filter out the header row if it's included in allRows (sheet_to_json with no header option often includes it)
        // And ensure we only take up to maxRows
        const dataRows = allRows.slice(0, maxRows);

        // Pad with empty objects if less than maxRows
        while (dataRows.length < maxRows) {
          dataRows.push({});
        }

        resolve({ headers, rows: dataRows });
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = (error) => {
      reject(error);
    };

    reader.readAsArrayBuffer(file);
  });
}

export function toHtmlTable(headers: string[], rows: Array<Record<string, any>>): string {
  if (!headers || headers.length === 0) {
    return '<p>No headers available for preview.</p>';
  }

  const thead = `<thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>`;

  const tbody = `<tbody>${rows.map(row => {
    const cells = headers.map(header => {
      const value = row[header] !== undefined && row[header] !== null ? String(row[header]) : '';
      return `<td>${value}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('')}</tbody>`;

  return `<table class="table table-striped">${thead}${tbody}</table>`;
}

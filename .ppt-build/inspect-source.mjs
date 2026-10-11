import fs from "node:fs/promises"; import {FileBlob,PresentationFile} from "@oai/artifact-tool";
const p=await PresentationFile.importPptx(await FileBlob.load("D:/newfoodcourt/The_Judiciary_Marathi_Presentation.pptx"));
console.log((await p.inspect({kind:"slide,textbox,shape,image,layout",maxChars:20000})).ndjson);
for(const [i,s] of p.slides.items.entries()){const b=await p.export({slide:s,format:"png",scale:1}); await fs.writeFile(`D:/newfoodcourt/.ppt-build/source-${String(i+1).padStart(2,"0")}.png`,new Uint8Array(await b.arrayBuffer()));}

"""Run the existing helpers with a fabricated brief and geometric pixels, without a model."""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]

def run(script,args,workspace,expect=0):
    result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),*args],cwd=workspace,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1'))
    if result.returncode!=expect:raise RuntimeError(script+' returned '+str(result.returncode)+': '+result.stderr[-1600:])
    return json.loads(result.stdout)if expect==0 else {'exit_code':result.returncode,'blocked':True}

def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();w=args.output.resolve()
    if w.exists()and any(w.iterdir()):parser.error('Use a new empty output directory.')
    w.mkdir(parents=True,exist_ok=True)
    brief=json.loads((ROOT/'examples/offline_brief.json').read_text(encoding='utf-8'));save(w/'brief.json',brief)
    catalog=run('validate_catalog.py',[],w);save(w/'catalog-validation.json',catalog)
    matched=run('match_styles.py',['--brief','brief.json','--top-k','3'],w);save(w/'matched-styles.json',matched)
    assert len(matched['selected'])==3 and len({r['family']for r in matched['selected']})==3
    prompts=[]
    for row in matched['selected']:
        prompt=run('build_prompt.py',['--brief','brief.json','--style-id',row['id']],w)
        assert prompt['exact_text']==brief['exact_text']
        prompts.append(prompt);save(w/('prompt-'+row['id']+'.json'),prompt)
    save(w/'prompt-packages.json',prompts)
    report={'direction_id':matched['selected'][0]['id'],'attempt':0,'issue_scope':'global','hard_checks':[],'soft_scores':dict.fromkeys(['communication','hierarchy_composition','style_brand_fit','lighting_material','legibility_export'],1),'synthetic':True}
    for key in ['brief_alignment','human_anatomy','spatial','lighting','object_integrity','text','count','scene_logic','domain']:
        report['hard_checks'].append({'id':key,'status':'uncertain'if key=='brief_alignment'else'not_applicable','severity':'critical','evidence':'OFFLINE SYNTHETIC PROTOCOL FIXTURE: no generated image exists; no visual check has been performed.','repair':'Requires a future real image and grounded inspection.'})
    save(w/'qa-uncertain-input.json',report)
    uncertain=run('qa_state.py',['--report','qa-uncertain-input.json'],w);assert uncertain['action']=='regenerate'and not uncertain['passed'];save(w/'qa-uncertain-result.json',uncertain)
    report['attempt']=2;save(w/'qa-limit-input.json',report)
    limit=run('qa_state.py',['--report','qa-limit-input.json'],w);assert limit['action']=='failed_preview'and not limit['passed'];save(w/'qa-limit-result.json',limit)
    image=Image.new('RGB',(320,180),'#082a38');draw=ImageDraw.Draw(image)
    draw.rectangle((12,12,307,167),outline='#f4df72',width=8)
    draw.rectangle((32,50,140,145),fill='#00b97b');draw.ellipse((160,30,275,145),fill='#ed805b')
    image.save(w/'synthetic-input.png');before=hashlib.sha256((w/'synthetic-input.png').read_bytes()).hexdigest()
    exported=run('export_image.py',['--input','synthetic-input.png','--output','synthetic-export.png','--width','480','--height','640','--background','#082a38'],w)
    exported['output']='synthetic-export.png';save(w/'export-report.json',exported)
    with Image.open(w/'synthetic-export.png')as output:assert output.size==(480,640)and not output.getexif()
    assert exported['padding']=={'left':0,'top':185,'right':0,'bottom':185}
    crop_guard=run('export_image.py',['--input','synthetic-input.png','--output','unapproved-crop.png','--width','200','--height','200','--mode','cover'],w,expect=2)
    assert not(w/'unapproved-crop.png').exists()
    overwrite_guard=run('export_image.py',['--input','synthetic-input.png','--output','synthetic-input.png','--width','200','--height','200'],w,expect=2)
    assert hashlib.sha256((w/'synthetic-input.png').read_bytes()).hexdigest()==before
    summary={'synthetic':True,'image_model_or_service_called':False,'reference_images_read_or_uploaded':False,'styles':catalog['styles'],'selected_style_ids':[r['id']for r in matched['selected']],'selected_families':[r['family']for r in matched['selected']],'prompt_packages':len(prompts),'exact_text_preserved':True,'QA_is_synthetic_input_not_visual_inspection':True,'QA_uncertain_action':uncertain['action'],'QA_limit_action':limit['action'],'export_source_pixels':[320,180],'export_pixels':[480,640],'padding':exported['padding'],'crop_without_approval_blocked':crop_guard['blocked'],'same_input_output_blocked':overwrite_guard['blocked'],'input_unchanged':True,'model_quality_or_host_session_tested':False}
    save(w/'validation.json',summary);print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()

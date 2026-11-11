param(
    [string]$SourcePath = 'C:\Users\happyelements\Desktop\Paper\英语 アンケート.txt',
    [string]$OutputDirectory = 'C:\Users\happyelements\Desktop\Paper\.en12v2_translation_58019ef83e5b4dfb8311c37c8f73c3ed\gdi_backup'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$gdiCode = @'
using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Globalization;

public static class QuestionnaireGdiPdf {
    const float PW = 595.2756f, PH = 841.8898f;
    class SourceLine { public int Id; public string Text; }
    class Page { public int Number; public List<SourceLine> Lines = new List<SourceLine>(); public List<Block> Blocks; }
    static Dictionary<int,int> used = new Dictionary<int,int>();
    static void Use(SourceLine l) { if(!used.ContainsKey(l.Id)) used[l.Id]=0; used[l.Id]++; }
    abstract class Block {
        public abstract float Measure(Renderer r, float w);
        public abstract void Draw(Renderer r,float x,float y,float w);
    }
    class Token { public string Text; public bool Box, Checked; public float Width; }
    class TextLine { public List<Token> Tokens = new List<Token>(); public float Width, Indent; }
    class RichLayout { public List<TextLine> Lines = new List<TextLine>(); public float Height, LineHeight; }
    class Renderer : IDisposable {
        public Graphics G; public float Body=10.5f, Density=1; public int Boxes, Checked;
        Dictionary<string,Font> fonts=new Dictionary<string,Font>();
        Dictionary<string,float> widths=new Dictionary<string,float>();
        public StringFormat Format = (StringFormat)StringFormat.GenericTypographic.Clone();
        public Renderer() { Format.FormatFlags |= StringFormatFlags.MeasureTrailingSpaces | StringFormatFlags.NoWrap; }
        public Font Font(float size,bool bold) {
            string key=size.ToString("F3",CultureInfo.InvariantCulture)+(bold?"b":"r");
            if(!fonts.ContainsKey(key)) fonts[key]=new Font("Arial",size,bold?FontStyle.Bold:FontStyle.Regular,GraphicsUnit.Point);
            return fonts[key];
        }
        public float Width(string text,Font f) {
            string key=f.SizeInPoints.ToString("F3",CultureInfo.InvariantCulture)+"|"+f.Style+"|"+text;
            if(!widths.ContainsKey(key)) widths[key]=G.MeasureString(text,f,10000,Format).Width;
            return widths[key];
        }
        public RichLayout Layout(string text,Font f,float w) {
            RichLayout result=new RichLayout();
            result.LineHeight=(float)Math.Ceiling(f.SizeInPoints*f.FontFamily.GetLineSpacing(f.Style)/f.FontFamily.GetEmHeight(f.Style));
            float sp=Width(" ",f); bool hanging=Regex.IsMatch(text,@"^\[(?: |x)\]");
            List<Token> tokens=new List<Token>();
            foreach(Match m in Regex.Matches(text,@"\[(?: |x)\]|\S+")) {
                string t=m.Value;
                if(t=="[ ]" || t=="[x]") tokens.Add(new Token{Text=t,Box=true,Checked=t=="[x]",Width=9.2f});
                else if(Width(t,f)>w-1) {
                    string part="";
                    foreach(char c in t) { if(part.Length>0 && Width(part+c,f)>w-1) {tokens.Add(new Token{Text=part,Width=Width(part,f)});part="";} part+=c; }
                    if(part.Length>0) tokens.Add(new Token{Text=part,Width=Width(part,f)});
                } else tokens.Add(new Token{Text=t,Width=Width(t,f)});
            }
            TextLine line=new TextLine();
            foreach(Token t in tokens) {
                float gap=line.Tokens.Count>0?sp:0;
                if(line.Tokens.Count>0 && line.Width+gap+t.Width>w-line.Indent+0.01f) {
                    result.Lines.Add(line); line=new TextLine(); line.Indent=hanging?12.5f:0; gap=0;
                }
                line.Tokens.Add(t);line.Width+=gap+t.Width;
            }
            if(line.Tokens.Count>0)result.Lines.Add(line);
            if(result.Lines.Count==0)result.Lines.Add(new TextLine());
            result.Height=result.Lines.Count*result.LineHeight;
            return result;
        }
        public float TextHeight(string text,Font f,float w) { return Layout(text,f,w).Height; }
        public void Text(string text,Font f,float x,float y,float w,bool center) {
            if(text=="↓") { using(Pen p=new Pen(Color.Black,1.1f)) { G.DrawLine(p,x+w/2,y+1,x+w/2,y+10); G.DrawLine(p,x+w/2-4,y+6,x+w/2,y+10);G.DrawLine(p,x+w/2+4,y+6,x+w/2,y+10); }return; }
            RichLayout layout=Layout(text,f,w);float sp=Width(" ",f);
            foreach(TextLine line in layout.Lines) {
                float tx=x+line.Indent+(center?(w-line.Indent-line.Width)/2:0);
                foreach(Token t in line.Tokens) {
                    if(t.Box) {
                        using(Pen p=new Pen(Color.Black,0.75f))G.DrawRectangle(p,tx,y+2,8.5f,8.5f);
                        if(t.Checked) using(Pen p=new Pen(Color.Black,1.1f)) {G.DrawLine(p,tx+1.4f,y+6.2f,tx+3.6f,y+8.6f);G.DrawLine(p,tx+3.6f,y+8.6f,tx+7.4f,y+3.5f);}
                        Boxes++;if(t.Checked)Checked++;
                    } else G.DrawString(t.Text,f,Brushes.Black,new PointF(tx,y),Format);
                    tx+=t.Width+sp;
                }
                y+=layout.LineHeight;
            }
        }
        public float ListHeight(List<Block> blocks,float w) {float h=0;foreach(Block b in blocks)h+=b.Measure(this,w);return h;}
        public void ListDraw(List<Block> blocks,float x,float y,float w) {foreach(Block b in blocks){float h=b.Measure(this,w);b.Draw(this,x,y,w);y+=h;}}
        public void Dispose(){foreach(Font f in fonts.Values)f.Dispose();Format.Dispose();}
    }
    class TextBlock:Block {
        public string Text,Role; public bool Center; public float Before,After;
        public TextBlock(string text,string role){Text=text;Role=role;Before=0;After=2.8f;if(role=="h1"){After=10;}if(role=="h2"){Before=6;After=5;}if(role=="h3"){Before=3;After=4;}if(role=="question"){After=5;}if(role=="option"){After=1.8f;}if(role=="cell"){After=0;}if(role=="arrow"){After=2;Center=true;}}
        Font GetFont(Renderer r){return r.Font(Role=="rulesHeader"?10:r.Body+(Role=="h1"?5:Role=="h2"?2:Role=="question"?0.3f:0),Role=="h1"||Role=="h2"||Role=="h3"||Role=="question"||Role=="header"||Role=="rulesHeader");}
        public override float Measure(Renderer r,float w){float pad=Role=="h2"?5:0;return Before*r.Density+r.TextHeight(Text,GetFont(r),w-pad*2)+(Role=="h2"?7:0)+After*r.Density;}
        public override void Draw(Renderer r,float x,float y,float w){y+=Before*r.Density;if(Role=="h2"){float h=r.TextHeight(Text,GetFont(r),w-10)+7;using(Brush b=new SolidBrush(Color.FromArgb(239,239,239)))r.G.FillRectangle(b,x,y,w,h);r.Text(Text,GetFont(r),x+5,y+3,w-10,false);}else r.Text(Text,GetFont(r),x,y,w,Center);}
    }
    class WritingBlock:Block {
        public int Lines;public float Minimum;
        public WritingBlock(int n,float min){Lines=n;Minimum=min;}
        public override float Measure(Renderer r,float w){return Minimum+7*r.Density;}
        public override void Draw(Renderer r,float x,float y,float w){using(Pen p=new Pen(Color.FromArgb(120,120,120),0.5f)){r.G.DrawRectangle(p,x,y+2,w,Minimum-2);for(int i=0;i<Lines;i++){float yy=y+Minimum*(i+1)/(Lines+1);r.G.DrawLine(p,x+8,yy,x+w-8,yy);}}}
    }
    class Cell {public List<Block> Blocks=new List<Block>();public bool Center;}
    class TableBlock:Block {
        public List<List<Cell>> Rows=new List<List<Cell>>();public float[] Fractions;public bool Header=true;public float Pad=3.5f;public float After=5;
        float[] Heights(Renderer r,float w){float[] heights=new float[Rows.Count];for(int i=0;i<Rows.Count;i++){float max=0;for(int j=0;j<Rows[i].Count;j++){float cellw=w*Fractions[j]-Pad*2;max=Math.Max(max,r.ListHeight(Rows[i][j].Blocks,cellw));}heights[i]=max+Pad*2;}return heights;}
        public override float Measure(Renderer r,float w){float h=2;foreach(float a in Heights(r,w))h+=a;return h+After*r.Density;}
        public override void Draw(Renderer r,float x,float y,float w){float[] heights=Heights(r,w);y+=2;using(Pen p=new Pen(Color.FromArgb(65,65,65),0.5f)){for(int i=0;i<Rows.Count;i++){float cx=x;for(int j=0;j<Rows[i].Count;j++){float cw=w*Fractions[j];if(i==0&&Header)using(Brush b=new SolidBrush(Color.FromArgb(242,242,242)))r.G.FillRectangle(b,cx,y,cw,heights[i]);r.G.DrawRectangle(p,cx,y,cw,heights[i]);Cell cell=Rows[i][j];float content=r.ListHeight(cell.Blocks,cw-Pad*2);r.ListDraw(cell.Blocks,cx+Pad,y+Pad+(cell.Center?(heights[i]-Pad*2-content)/2:0),cw-Pad*2);cx+=cw;}y+=heights[i];}}}
    }
    class ColumnsBlock:Block {
        public Block Left;public List<Block> Right;const float Gap=10;
        public override float Measure(Renderer r,float w){float left=(w-Gap)*0.51f,right=w-Gap-left;return Math.Max(Left.Measure(r,left),r.ListHeight(Right,right-10)+10)+5*r.Density;}
        public override void Draw(Renderer r,float x,float y,float w){float left=(w-Gap)*0.51f,right=w-Gap-left;Left.Draw(r,x,y,left);float h=r.ListHeight(Right,right-10)+10;using(Pen p=new Pen(Color.FromArgb(70,70,70),0.5f))r.G.DrawRectangle(p,x+left+Gap,y,right,h);r.ListDraw(Right,x+left+Gap+5,y+5,right-10);}
    }
    static bool TableLine(SourceLine l){return l.Text.Contains("|");}
    static bool Separator(SourceLine l){return Regex.IsMatch(l.Text,@"^\|?\s*:?-{3,}");}
    static TextBlock Make(SourceLine line,string role){Use(line);return new TextBlock(line.Text,role);}
    static List<string> Cells(string text){string s=text.Trim();if(s.StartsWith("|"))s=s.Substring(1);if(s.EndsWith("|"))s=s.Substring(0,s.Length-1);List<string>a=new List<string>();foreach(string c in s.Split('|'))a.Add(c.Trim());return a;}
    static List<Block> Standard(List<SourceLine> lines,int page){
        List<Block> blocks=new List<Block>();
        for(int i=0;i<lines.Count;i++){
            SourceLine line=lines[i];
            if(TableLine(line)){List<SourceLine>group=new List<SourceLine>();group.Add(line);while(i+1<lines.Count&&TableLine(lines[i+1]))group.Add(lines[++i]);string type=(page==2||page==3)?"rules":page==4?"conservation":"general";blocks.Add(NativeTable(group,type));}
            else if(Regex.IsMatch(line.Text,@"^_{10,}$")){int n=1;Use(line);while(i+1<lines.Count&&Regex.IsMatch(lines[i+1].Text,@"^_{10,}$")){Use(lines[++i]);n++;}float height=page==12?204:page==2||page==3?73:page==11?64:64;blocks.Add(new WritingBlock(n,height));}
            else {string role=Regex.IsMatch(line.Text,@"^\d+\. ")?"h2":line.Text.StartsWith("Q")?"question":line.Text=="Guidance for completing the questionnaire"?"h1":line.Text=="Survey details"?"h2":Regex.IsMatch(line.Text,@"^(How to answer|Example of a completed response|Activity reference list)")?"h3":line.Text=="↓"?"arrow":line.Text.StartsWith("[ ]")||line.Text.StartsWith("[x]")?"option":"body";blocks.Add(Make(line,role));}
        }return blocks;
    }
    static TableBlock NativeTable(List<SourceLine> lines,string type){
        TableBlock table=new TableBlock();table.Fractions=type=="rules"?new float[]{.40f,.12f,.12f,.12f,.12f,.12f}:type=="conservation"?new float[]{.53f,.18f,.29f}:type=="stakeholders"?new float[]{.73f,.27f}:new float[]{.5f,.5f};if(type=="rules")table.Pad=3;
        foreach(SourceLine line in lines){Use(line);if(Separator(line))continue;List<string>parts=Cells(line.Text);if(parts.Count!=table.Fractions.Length)throw new Exception("Table column mismatch at source line "+line.Id);List<Cell>row=new List<Cell>();for(int j=0;j<parts.Count;j++){Cell c=new Cell();TextBlock tb=new TextBlock(parts[j],table.Rows.Count==0?(type=="rules"?"rulesHeader":"header"):"cell");if(type=="rules"&&j>0){tb.Center=true;c.Center=true;}if(type=="conservation"&&j>0){tb.Center=true;c.Center=true;}c.Blocks.Add(tb);row.Add(c);}table.Rows.Add(row);}return table;
    }
    static List<Block> Q3(Page p){
        int first=p.Lines.FindIndex(TableLine),end=first;while(end<p.Lines.Count&&TableLine(p.Lines[end]))end++;int arrow=p.Lines.FindIndex(l=>l.Text=="↓");int refend=arrow<0?p.Lines.Count:arrow;
        List<Block>b=Standard(p.Lines.GetRange(0,first),p.Number);ColumnsBlock c=new ColumnsBlock();c.Left=NativeTable(p.Lines.GetRange(first,end-first),"stakeholders");c.Right=Standard(p.Lines.GetRange(end,refend-end),p.Number);b.Add(c);if(arrow>=0)b.AddRange(Standard(p.Lines.GetRange(arrow,p.Lines.Count-arrow),p.Number));return b;
    }
    static List<Block> Q4(Page p){
        List<int> starts=new List<int>();for(int i=0;i<p.Lines.Count;i++)if(Regex.IsMatch(p.Lines[i].Text,@"^\(\d+\) "))starts.Add(i);int suffix=p.Lines.FindIndex(l=>l.Text.StartsWith("If you use any approaches"));int end=suffix<0?p.Lines.Count:suffix;
        List<Block>b=new List<Block>();TableBlock t=new TableBlock();t.Fractions=new float[]{.37f,.63f};t.Header=false;t.Pad=4;
        if(starts[0]>0){b.Add(Make(p.Lines[0],"question"));List<Cell>head=new List<Cell>();for(int i=1;i<3;i++){Cell cell=new Cell();cell.Blocks.Add(Make(p.Lines[i],"header"));head.Add(cell);}t.Rows.Add(head);t.Header=true;}
        for(int i=0;i<starts.Count;i++){int stop=i+1<starts.Count?starts[i+1]:end;List<SourceLine>g=p.Lines.GetRange(starts[i],stop-starts[i]);if(g.Count!=7)throw new Exception("Q4 group count "+g.Count);Cell left=new Cell(),right=new Cell();left.Blocks.Add(Make(g[0],"body"));right.Blocks.Add(Make(g[1],"question"));right.Blocks.Add(Make(g[2],"body"));for(int k=3;k<g.Count;k++)right.Blocks.Add(Make(g[k],"option"));t.Rows.Add(new List<Cell>{left,right});}b.Add(t);if(suffix>=0)b.AddRange(Standard(p.Lines.GetRange(suffix,p.Lines.Count-suffix),p.Number));return b;
    }
    static List<Block> Q5(Page p){
        int suffix=p.Lines.FindIndex(l=>l.Text.StartsWith("For the approaches described above"));int end=suffix<0?p.Lines.Count:suffix;List<int>starts=new List<int>();for(int i=0;i<end;i++)if(Regex.IsMatch(p.Lines[i].Text,@"^\(\d+\) "))starts.Add(i);
        List<Block>b=new List<Block>();TableBlock t=new TableBlock();t.Fractions=new float[]{.65f,.35f};t.Header=false;t.Pad=4;
        if(starts[0]>0){b.AddRange(Standard(p.Lines.GetRange(0,2),p.Number));List<Cell>head=new List<Cell>();for(int i=2;i<4;i++){Cell cell=new Cell();cell.Blocks.Add(Make(p.Lines[i],"header"));head.Add(cell);}t.Rows.Add(head);t.Header=true;}
        for(int i=0;i<starts.Count;i++){int stop=i+1<starts.Count?starts[i+1]:end;Cell left=new Cell(),right=new Cell();int options=0;foreach(SourceLine l in p.Lines.GetRange(starts[i],stop-starts[i])){if(l.Text.StartsWith("[ ]")){right.Blocks.Add(Make(l,"option"));options++;}else left.Blocks.Add(Make(l,"body"));}if(options!=3)throw new Exception("Q5 option count");t.Rows.Add(new List<Cell>{left,right});}b.Add(t);if(suffix>=0)b.AddRange(Standard(p.Lines.GetRange(suffix,p.Lines.Count-suffix),p.Number));return b;
    }
    static void Ascii(Stream stream,string text){byte[]b=Encoding.ASCII.GetBytes(text);stream.Write(b,0,b.Length);}
    static void Pdf(string path,List<string> images){
        int count=2+images.Count*3+1;long[]offsets=new long[count+1];using(FileStream f=new FileStream(path,FileMode.Create,FileAccess.Write)){
            Ascii(f,"%PDF-1.4\n%");f.Write(new byte[]{0xe2,0xe3,0xcf,0xd3},0,4);Ascii(f,"\n");
            offsets[1]=f.Position;Ascii(f,"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n");
            offsets[2]=f.Position;Ascii(f,"2 0 obj\n<< /Type /Pages /Count "+images.Count+" /Kids [");for(int i=0;i<images.Count;i++)Ascii(f,(3+3*i)+" 0 R ");Ascii(f,"] >>\nendobj\n");
            for(int i=0;i<images.Count;i++){
                int page=3+i*3,content=page+1,img=page+2;byte[]bytes=File.ReadAllBytes(images[i]);string commands="q\n595.2756 0 0 841.8898 0 0 cm\n/Im0 Do\nQ\n";
                offsets[page]=f.Position;Ascii(f,page+" 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.2756 841.8898] /Resources << /XObject << /Im0 "+img+" 0 R >> >> /Contents "+content+" 0 R >>\nendobj\n");
                offsets[content]=f.Position;Ascii(f,content+" 0 obj\n<< /Length "+Encoding.ASCII.GetByteCount(commands)+" >>\nstream\n"+commands+"endstream\nendobj\n");
                offsets[img]=f.Position;Ascii(f,img+" 0 obj\n<< /Type /XObject /Subtype /Image /Width 2480 /Height 3508 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length "+bytes.Length+" >>\nstream\n");f.Write(bytes,0,bytes.Length);Ascii(f,"\nendstream\nendobj\n");
            }
            offsets[count]=f.Position;Ascii(f,count+" 0 obj\n<< /Title (Questionnaire for park managers) /Creator (System.Drawing GDI form renderer) /Producer (Local image PDF writer) >>\nendobj\n");long xref=f.Position;Ascii(f,"xref\n0 "+(count+1)+"\n0000000000 65535 f \n");for(int i=1;i<=count;i++)Ascii(f,offsets[i].ToString("D10",CultureInfo.InvariantCulture)+" 00000 n \n");Ascii(f,"trailer\n<< /Size "+(count+1)+" /Root 1 0 R /Info "+count+" 0 R >>\nstartxref\n"+xref+"\n%%EOF\n");
        }
    }
    public static string Run(string sourcePath,string outputDirectory){
        Directory.CreateDirectory(outputDirectory);used.Clear();string source=File.ReadAllText(sourcePath,Encoding.UTF8).TrimStart('\ufeff');List<Page>pages=new List<Page>();Page current=null;string[]all=Regex.Split(source,@"\r?\n");int nonempty=0;
        for(int i=0;i<all.Length;i++){string line=all[i].Trim();Match m=Regex.Match(line,@"^PAGE (\d+)$");if(m.Success){current=new Page{Number=int.Parse(m.Groups[1].Value)};pages.Add(current);}else if(line.Length>0){if(current==null)throw new Exception("Text before PAGE");current.Lines.Add(new SourceLine{Id=i+1,Text=line});nonempty++;}}
        if(pages.Count!=12)throw new Exception("Expected 12 pages");int sourceBoxes=Regex.Matches(source,@"\[(?: |x)\]").Count,sourceChecked=Regex.Matches(source,@"\[x\]").Count;if(sourceBoxes!=263||sourceChecked!=12)throw new Exception("Unexpected source box counts");
        foreach(Page p in pages){if(p.Number==5||p.Number==6)p.Blocks=Q3(p);else if(p.Number==7||p.Number==8)p.Blocks=Q4(p);else if(p.Number==9||p.Number==10)p.Blocks=Q5(p);else if(p.Number==1){p.Blocks=new List<Block>();p.Blocks.Add(Make(p.Lines[0],"h1"));p.Blocks.AddRange(Standard(p.Lines.GetRange(1,p.Lines.Count-1),p.Number));}else p.Blocks=Standard(p.Lines,p.Number);}
        foreach(Page p in pages)foreach(SourceLine l in p.Lines)if(!used.ContainsKey(l.Id)||used[l.Id]!=1)throw new Exception("Source coverage mismatch "+l.Id);
        List<string>images=new List<string>();StringBuilder audit=new StringBuilder();audit.Append("{\"pages\":12,\"dpi\":300,\"sourceLines\":"+nonempty+",\"everySourceLineRenderedExactlyOnce\":true,\"pageLayout\":[");int renderedBoxes=0,renderedChecked=0;
        using(Renderer r=new Renderer()){
            for(int index=0;index<pages.Count;index++){
                Page p=pages[index];using(Bitmap bitmap=new Bitmap(2480,3508,PixelFormat.Format24bppRgb)){bitmap.SetResolution(300,300);using(Graphics g=Graphics.FromImage(bitmap)){r.G=g;g.PageUnit=GraphicsUnit.Point;g.SmoothingMode=SmoothingMode.HighQuality;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;g.Clear(Color.White);r.Boxes=0;r.Checked=0;
                    float margin=24,top=24,bottom=PH-30,height=0;bool fit=false;float[]sizes=p.Number==1||p.Number==12?new float[]{11,10.75f,10.5f,10.25f,10}:new float[]{10.5f,10.25f,10};
                    for(int density=0;density<3&&!fit;density++){r.Density=density==0?1:density==1?.85f:.70f;margin=density==2?18:24;top=density==2?18:24;bottom=PH-(density==2?25:30);foreach(float size in sizes){r.Body=size;height=r.ListHeight(p.Blocks,PW-2*margin);if(height<=bottom-top){fit=true;break;}}}
                    if(!fit)throw new Exception("Page "+p.Number+" does not fit at 10pt: "+height.ToString("F2")+" pt");
                    r.ListDraw(p.Blocks,margin,top,PW-2*margin);r.Text(p.Number.ToString(),r.Font(10,false),margin,PH-20,PW-2*margin,true);
                    int expected=Regex.Matches(String.Join("\n",p.Lines.ConvertAll(l=>l.Text).ToArray()),@"\[(?: |x)\]").Count;int expectedChecked=Regex.Matches(String.Join("\n",p.Lines.ConvertAll(l=>l.Text).ToArray()),@"\[x\]").Count;if(r.Boxes!=expected||r.Checked!=expectedChecked)throw new Exception("Rendered checkbox count mismatch on page "+p.Number);
                    renderedBoxes+=r.Boxes;renderedChecked+=r.Checked;
                    string stem=Path.Combine(outputDirectory,"page_"+p.Number.ToString("D2"));bitmap.Save(stem+".png",ImageFormat.Png);ImageCodecInfo codec=null;foreach(ImageCodecInfo c in ImageCodecInfo.GetImageEncoders())if(c.MimeType=="image/jpeg")codec=c;using(EncoderParameters ep=new EncoderParameters(1)){ep.Param[0]=new EncoderParameter(System.Drawing.Imaging.Encoder.Quality,96L);bitmap.Save(stem+".jpg",codec,ep);}images.Add(stem+".jpg");
                    if(index>0)audit.Append(",");audit.Append("{\"page\":"+p.Number+",\"fontPt\":"+r.Body.ToString("F2",CultureInfo.InvariantCulture)+",\"marginPt\":"+margin.ToString("F1",CultureInfo.InvariantCulture)+",\"spacingDensity\":"+r.Density.ToString("F2",CultureInfo.InvariantCulture)+",\"contentHeightPt\":"+height.ToString("F2",CultureInfo.InvariantCulture)+",\"availableHeightPt\":"+(bottom-top).ToString("F2",CultureInfo.InvariantCulture)+",\"verticalOverflowPt\":0,\"checkboxes\":"+r.Boxes+",\"checked\":"+r.Checked+"}");
                    Console.WriteLine("Page "+p.Number+": "+r.Body.ToString("F2")+"pt, "+height.ToString("F1")+"/"+(bottom-top).ToString("F1")+"pt, boxes="+r.Boxes+", checked="+r.Checked);
                }}
            }
        }
        if(renderedBoxes!=263||renderedChecked!=12)throw new Exception("Final checkbox counts mismatch");audit.Append("],\"checkboxes\":"+renderedBoxes+",\"checkedExamples\":"+renderedChecked+",\"textLayer\":false}");File.WriteAllText(Path.Combine(outputDirectory,"layout_audit.json"),audit.ToString(),new UTF8Encoding(false));string pdfPath=Path.Combine(outputDirectory,"questionnaire_gdi_backup.pdf");Pdf(pdfPath,images);return pdfPath;
    }
}
'@
Add-Type -TypeDefinition $gdiCode -ReferencedAssemblies System.Drawing
$gdiPdfResult = [QuestionnaireGdiPdf]::Run($SourcePath, $OutputDirectory)
Write-Output "PDF: $gdiPdfResult"

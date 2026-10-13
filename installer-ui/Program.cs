using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace XgimiInstaller {
 static class Program {
  [STAThread] static int Main(string[] args) {
   Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
   if(args.Length > 0 && args[0] == "--self-test") {
    if(InstallerForm.Quote("a b") != "\"a b\"" || InstallerForm.Quote("a\\") != "\"a\\\\\"") return 2;
    if(InstallerForm.Address("127.0.0.1") != "127.0.0.1:5555") return 3;
    try { InstallerForm.Address("x & whoami"); return 4; } catch(ArgumentException) {}
    if(!InstallerForm.SelfTestBackups()) return 6;
    var form = new InstallerForm(); form.Show(); Application.DoEvents();
    if(!form.CheckDescriptions()) return 5;
    form.SelectTask(1); Application.DoEvents();
    form.Shot(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"ui-smoke.png"));
    if(args.Length > 1) { // developer aid: screenshots of other pages into the given folder
     form.SelectTask(0); Application.DoEvents(); form.Shot(Path.Combine(args[1],"page-check.png"));
     form.SelectTask(3); Application.DoEvents(); form.Shot(Path.Combine(args[1],"page-remove.png"));
     form.SelectTask(4); form.SelectAdvanced(4); Application.DoEvents(); form.Shot(Path.Combine(args[1],"page-advanced-prepare.png"));
     form.SelectAdvanced(0); Application.DoEvents(); form.Shot(Path.Combine(args[1],"page-advanced-remote.png"));
     form.SelectAdvanced(5); Application.DoEvents(); form.Shot(Path.Combine(args[1],"page-advanced-plan.png"));
    }
    form.Close(); return 0;
   }
   Application.Run(new InstallerForm()); return 0;
  }
 }

 /// <summary>One operation the window can run: what it is called, which launch.py command it starts and which options it needs.</summary>
 sealed class Job {
  public string Title, Command, RunText, Description, Confirm, BackupFile, BackupName;
  public bool Prepare, Beam, Plan, Remote;
  public Job(string title, string command, string runText, string description) { Title=title; Command=command; RunText=runText; Description=description; }
  public Job WithRemote() { Remote=true; return this; }
  public Job With(string backupFile,string backupName) { BackupFile=backupFile; BackupName=backupName; return this; }
  public Job WithPrep(bool prepare,bool beam,bool plan) { Prepare=prepare; Beam=beam; Plan=plan; return this; }
 }

 public sealed class InstallerForm : Form {
  readonly string bundle = Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"kit");
  readonly TextBox ip = new TextBox(), log = new TextBox();
  readonly ListBox tasks = new ListBox();
  readonly ComboBox advanced = new ComboBox(), timezone = new ComboBox();
  readonly CheckBox services = new CheckBox(), beam = new CheckBox(), remote = new CheckBox();
  readonly Button start = new Button(), backupBrowse = new Button(), toggleLog = new Button();
  readonly Label title = new Label(), description = new Label(), backupLabel = new Label(), banner = new Label();
  readonly Panel prepare = new Panel(), backupRow = new Panel();
  Control zoneRow, servicesNote, remoteNote;
  readonly ProgressBar progress = new ProgressBar();
  string backupPath = "";
  bool running;

  readonly Job[] main = {
   new Job("Проверить проектор","check","Проверить",
    "Проверяет подключение, модель проектора, версию прошивки и совместимость системных приложений с русификатором.\r\n\r\nНичего не меняет. С этого стоит начать."),
   new Job("Установить русификацию","prepare-install","Установить",
    "Для проектора, на котором русификатора ещё нет. Включает русский язык, создаёт нужные базы данных, ставит перевод и автозапуск, чтобы перевод сохранялся после перезагрузки.\r\n\r\nПеред изменениями создаются резервные копии. Если русский язык ещё не был включён, понадобится одна перезагрузка проектора и повторный запуск этого же пункта. Если русификатор уже установлен, установщик предложит обновление.\r\n\r\nНиже можно сразу отметить всё остальное, что может понадобиться при первой настройке, и сделать это одним запуском. В конце установщик сам перезагрузит проектор и завершит настройку (2–4 минуты).").WithPrep(true,true,false).WithRemote(),
   new Job("Обновить русификацию","update-boot","Обновить",
    "Для проектора, на котором русификатор уже стоит. Ставит новую версию перевода и сохраняет прежние настройки. Язык, часовой пояс и сервисы не меняются.\r\n\r\nПосле обновления желательно перезагрузить проектор."),
   new Job("Удалить русификацию","remove-autostart","Удалить",
    "Убирает перевод и автозапуск и возвращает данные из резервной копии, сделанной при установке. После перезагрузки проектор снова будет на китайском.\r\n\r\nУдалить можно только с того компьютера, на котором выполнялась установка: резервные копии лежат в папке kit\\runs.").With("setup.json","установки"),
   new Job("Дополнительно…","","Выполнить","Редкие операции: кнопки пульта, подготовка языка и часового пояса отдельно от установки, лаунчер BEAM, восстановление после прерванной установки.")
  };
  readonly Job[] extra;
  readonly string[] zones = {"", "Europe/Moscow","Europe/Kaliningrad","Europe/Samara","Asia/Yekaterinburg","Asia/Omsk","Asia/Novosibirsk","Asia/Krasnoyarsk","Asia/Irkutsk","Asia/Yakutsk","Asia/Vladivostok","Asia/Magadan","Asia/Kamchatka","Europe/Minsk","Europe/Kyiv","Asia/Almaty","Europe/Berlin","Europe/London","UTC"};
  readonly string[] zoneNames = {"Не менять","Москва (UTC+3)","Калининград (UTC+2)","Самара (UTC+4)","Екатеринбург (UTC+5)","Омск (UTC+6)","Новосибирск (UTC+7)","Красноярск (UTC+7)","Иркутск (UTC+8)","Якутск (UTC+9)","Владивосток (UTC+10)","Магадан (UTC+11)","Камчатка (UTC+12)","Минск (UTC+3)","Киев (UTC+2)","Алма-Ата (UTC+5)","Берлин (UTC+1)","Лондон (UTC+0)","UTC"};

  public InstallerForm() {
   extra = new Job[] {
    (new Job("Кнопки пульта: установить или обновить","install-remote","Выполнить",
     "Ставит независимый модуль, который позволяет назначать действия на кнопки пульта. Работает с любым лаунчером. При первой установке включается автозапуск, при обновлении сохраняются назначения.\r\n\r\nПосле установки нужна полная перезагрузка. Назначения настраиваются в штатных настройках: Общее → Кнопки пульта.")),
    (new Job("Кнопки пульта: включить","enable-remote","Включить",
     "Включает автозапуск уже установленного модуля кнопок и проверяет его службы. Сохранённые назначения применяются снова.")),
    (new Job("Кнопки пульта: отключить","disable-remote","Отключить",
     "Отключает автозапуск модуля кнопок и останавливает его. Назначения сохраняются, кнопки возвращаются к штатным обработчикам.")),
    (new Job("Кнопки пульта: восстановить после сбоя","recover-remote","Восстановить",
     "Возвращает состояние автозапуска после прерванного обновления кнопок. Используется журнал последнего обновления из папки kit\\runs.")).With("remote-setup.json","обновления кнопок"),
    (new Job("Подготовить язык, часовой пояс и сервисы","prepare","Подготовить",
     "Включает русский язык, нужный часовой пояс, создаёт базы данных быстрой панели и Atmosphere. Перевод при этом не устанавливается. При смене языка понадобится перезагрузка.\r\n\r\nЛаунчер BEAM ставится только если отметить его ниже.")).WithPrep(true,true,false),
    (new Job("Показать текущее состояние подготовки","prepare","Показать",
     "Показывает текущий язык, часовой пояс и состояние сервисов. Ничего не применяет и не устанавливает.")).WithPrep(false,false,true),
    (new Job("Отменить подготовку","undo-prepare","Отменить",
     "Возвращает язык, часовой пояс, клавиатуру и состояние сервисов из резервной копии подготовки. Изменения, сделанные вами независимо, сохраняются. Установленный BEAM и созданные базы данных не удаляются.")).With("preparation.json","подготовки"),
    (new Job("Вернуть отключённые лаунчеры","restore-launchers","Вернуть",
     "Возвращает прежнее состояние сторонних лаунчеров, которые были отключены при установке BEAM. BEAM и его остальные настройки сохраняются.")).With("beam-setup.json","установки BEAM"),
    (new Job("Восстановить после прерванной установки","recover-autostart","Восстановить",
     "Возвращает исходное состояние, если первая установка была прервана. Используется резервная копия последней установки из папки kit\\runs.")).With("setup.json","установки"),
    (new Job("Завершить настройку (перезагрузка и включение служб)","finish-setup","Завершить",
     "Перезагружает проектор и заново включает службы автозапуска (перевод и кнопки пульта). Нужно, если установка прервалась, проектор выключили до её окончания или после перезагрузки перевод не применился.\r\n\r\nЗанимает 2–4 минуты. Если проектор после перезагрузки останется выключенным, включите его с пульта: установщик ждёт до 10 минут."))
   };
   Text="XGIMI — установка русификации"; Size=new Size(980,880); MinimumSize=new Size(900,780);
   StartPosition=FormStartPosition.CenterScreen; Font=new Font("Segoe UI",10); BackColor=Color.FromArgb(245,247,250);
   Build();
   foreach(Job j in main) tasks.Items.Add(j.Title);
   foreach(Job j in extra) advanced.Items.Add(j.Title);
   advanced.SelectedIndex=0; tasks.SelectedIndex=0;
   LoadSettings();
   FormClosing+=delegate(object sender,FormClosingEventArgs e) {if(running) {e.Cancel=true; MessageBox.Show("Дождитесь завершения операции. Закрытие может прервать установку.",Text);}};
  }

  // ---------- window ----------
  void Build() {
   var root=new TableLayoutPanel { Dock=DockStyle.Fill, Padding=new Padding(20,16,20,16), ColumnCount=1, RowCount=7 };
   Controls.Add(root);
   root.Controls.Add(new Label {Text="Русификация XGIMI Play 6",AutoSize=true,Font=new Font("Segoe UI",20,FontStyle.Bold),Margin=new Padding(0,0,0,0)},0,0);
   root.Controls.Add(new Label {Text="Прошивка v1.7.116 · Android 11 · перевод 1.19.44 · установщик 1.16",AutoSize=true,ForeColor=Color.DimGray,Margin=new Padding(0,0,0,10)},0,1);

   // connection
   var connection=new GroupBox {Text=" 1. Подключение ",Dock=DockStyle.Fill,Height=72,Padding=new Padding(12,6,12,8),Margin=new Padding(0,0,0,10)};
   var conn=new FlowLayoutPanel {Dock=DockStyle.Fill,FlowDirection=FlowDirection.LeftToRight,WrapContents=true};
   conn.Controls.Add(new Label {Text="IP проектора:",AutoSize=true,Padding=new Padding(0,6,6,0)});
   ip.Width=210; conn.Controls.Add(ip);
   conn.Controls.Add(new Label {Text="например 192.168.1.50 (порт 5555 подставится сам)",AutoSize=true,ForeColor=Color.DimGray,Padding=new Padding(8,6,0,0)});
   var adbHelp=new LinkLabel {Text="Как включить ADB",AutoSize=true,Padding=new Padding(16,6,0,0)};
   adbHelp.Click+=delegate {MessageBox.Show("Компьютер и проектор должны быть в одной сети.\r\n\r\n1. Скачайте на компьютер приложение SystemUI Tuner.\r\n\r\n2. Поставьте SystemUI Tuner на проектор: добавьте к имени файла .1 (получится …apk.1) и скопируйте файл на флешку. На проекторе: файловый менеджер → файл → OK → «Другие действия» → установщик APK → «Открыть один раз» → установить.\r\n\r\n3. Включите ADB в SystemUI Tuner.\r\n\r\n4. Узнайте IP проектора в настройках сети или в списке устройств роутера и введите его в окне установщика.\r\n\r\nЕсли не получается: нажмите «Проверить проектор» — установщик подскажет, что именно не так.","Как включить ADB",MessageBoxButtons.OK,MessageBoxIcon.Information);};
   conn.Controls.Add(adbHelp);
   connection.Controls.Add(conn);
   root.Controls.Add(connection,0,2);

   // choice: task list + details
   var choice=new GroupBox {Text=" 2. Что сделать ",Dock=DockStyle.Fill,Padding=new Padding(10,6,10,10),Margin=new Padding(0,0,0,10)};
   var split=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=2,RowCount=1};
   split.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,270)); split.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
   tasks.Dock=DockStyle.Fill; tasks.IntegralHeight=false; tasks.DrawMode=DrawMode.OwnerDrawFixed; tasks.ItemHeight=42; tasks.BorderStyle=BorderStyle.None; tasks.BackColor=Color.White;
   tasks.DrawItem+=DrawTask; tasks.SelectedIndexChanged+=delegate {ShowTask();};
   split.Controls.Add(tasks,0,0);
   var detail=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=1,RowCount=5,Padding=new Padding(16,2,4,0),AutoScroll=true};
   title.AutoSize=true; title.Font=new Font("Segoe UI",13,FontStyle.Bold); title.Margin=new Padding(0,0,0,6); detail.Controls.Add(title,0,0);
   advanced.DropDownStyle=ComboBoxStyle.DropDownList; advanced.Dock=DockStyle.Top; advanced.Margin=new Padding(0,0,0,10); advanced.SelectedIndexChanged+=delegate {ShowTask();}; detail.Controls.Add(advanced,0,1);
   description.AutoSize=true; description.MaximumSize=new Size(600,0); description.Margin=new Padding(0,0,0,10); detail.Controls.Add(description,0,2);
   BuildPrepare(); detail.Controls.Add(prepare,0,3);
   BuildBackup(); detail.Controls.Add(backupRow,0,4);
   split.Controls.Add(detail,1,0);
   choice.Controls.Add(split);
   root.Controls.Add(choice,0,3);

   // run
   var run=new FlowLayoutPanel {AutoSize=true,Dock=DockStyle.Fill,Margin=new Padding(0,0,0,6)};
   start.Width=180; start.Height=40; start.BackColor=Color.FromArgb(35,100,210); start.ForeColor=Color.White; start.FlatStyle=FlatStyle.Flat; start.Font=new Font("Segoe UI",11,FontStyle.Bold);
   start.Click+=async delegate {await Execute();}; run.Controls.Add(start);
   var logs=new Button {Text="Журналы",Width=110,Height=40}; logs.Click+=delegate {Open(Path.Combine(bundle,"runs"));}; run.Controls.Add(logs);
   var help=new Button {Text="Инструкция",Width=120,Height=40}; help.Click+=delegate {Open(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"START-HERE.txt"));}; run.Controls.Add(help);
   root.Controls.Add(run,0,4);

   // result
   var result=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=1,RowCount=3,AutoSize=true};
   banner.AutoSize=false; banner.Dock=DockStyle.Top; banner.Height=78; banner.Padding=new Padding(12,8,12,8); banner.Font=new Font("Segoe UI",10.5f,FontStyle.Bold); banner.TextAlign=ContentAlignment.MiddleLeft;
   SetBanner("info","Выберите действие и нажмите кнопку. Пока ничего не менялось.");
   result.Controls.Add(banner,0,0);
   progress.Dock=DockStyle.Top; progress.Height=6; progress.Margin=new Padding(0,4,0,4); result.Controls.Add(progress,0,1);
   toggleLog.Text="Подробности ▾"; toggleLog.AutoSize=true; toggleLog.FlatStyle=FlatStyle.Flat; toggleLog.FlatAppearance.BorderSize=0; toggleLog.ForeColor=Color.FromArgb(35,100,210);
   toggleLog.Click+=delegate {SetLogVisible(!log.Visible);}; result.Controls.Add(toggleLog,0,2);
   root.Controls.Add(result,0,5);
   log.Multiline=true; log.ReadOnly=true; log.ScrollBars=ScrollBars.Both; log.WordWrap=false; log.Dock=DockStyle.Fill; log.Font=new Font("Consolas",9.5f); log.BackColor=Color.White; log.Height=130; log.Visible=false;
   root.Controls.Add(log,0,6);
   for(int i=0;i<6;i++) root.RowStyles.Add(new RowStyle(i==3?SizeType.Percent:SizeType.AutoSize,i==3?100:0));
   root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
  }
  void BuildPrepare() {
   prepare.Dock=DockStyle.Top; prepare.AutoSize=true; prepare.Margin=new Padding(0,0,0,10);
   var f=new FlowLayoutPanel {Dock=DockStyle.Top,AutoSize=true,FlowDirection=FlowDirection.TopDown,WrapContents=false};
   var zones_=new FlowLayoutPanel {AutoSize=true,FlowDirection=FlowDirection.LeftToRight}; zoneRow=zones_;
   zones_.Controls.Add(new Label {Text="Часовой пояс:",AutoSize=true,Padding=new Padding(0,5,6,0)});
   timezone.DropDownStyle=ComboBoxStyle.DropDownList; timezone.Width=240; foreach(string name in zoneNames) timezone.Items.Add(name); timezone.SelectedIndex=0; zones_.Controls.Add(timezone);
   f.Controls.Add(zones_);
   services.Text="Отключить фоновые китайские сервисы XGIMI (реклама, отчёты, магазин и др.)"; services.AutoSize=true; services.Margin=new Padding(0,8,0,0); f.Controls.Add(services);
   var note=new Label {Text="Приложения не удаляются; отключение можно отменить.",AutoSize=true,ForeColor=Color.DimGray,Margin=new Padding(22,0,0,0)}; servicesNote=note; f.Controls.Add(note);
   beam.Text="Установить лаунчер BEAM (скачивается из интернета; права, кнопка «Домой»)"; beam.AutoSize=true; beam.Margin=new Padding(0,8,0,0); f.Controls.Add(beam);
   remote.Text="Установить модуль кнопок пульта"; remote.AutoSize=true; remote.Margin=new Padding(0,8,0,0); f.Controls.Add(remote);
   var rnote=new Label {Text="Позволяет назначать действия на кнопки пульта. Работает с любым лаунчером.",AutoSize=true,ForeColor=Color.DimGray,Margin=new Padding(22,0,0,0)}; remoteNote=rnote; f.Controls.Add(rnote);
   prepare.Controls.Add(f);
  }
  void BuildBackup() {
   backupRow.Dock=DockStyle.Top; backupRow.AutoSize=true; backupRow.Margin=new Padding(0);
   var f=new FlowLayoutPanel {Dock=DockStyle.Top,AutoSize=true,FlowDirection=FlowDirection.LeftToRight};
   backupLabel.AutoSize=true; backupLabel.MaximumSize=new Size(470,0); backupLabel.Padding=new Padding(0,6,8,0); f.Controls.Add(backupLabel);
   backupBrowse.Text="Другая…"; backupBrowse.Width=100; backupBrowse.Height=30; f.Controls.Add(backupBrowse);
   backupBrowse.Click+=delegate {using(var picker=new FolderBrowserDialog {Description="Выберите папку резервной копии из kit\\runs",SelectedPath=Path.Combine(bundle,"runs")}) {if(picker.ShowDialog()==DialogResult.OK) {backupPath=picker.SelectedPath; ShowBackup();}}};
   backupRow.Controls.Add(f);
  }
  void DrawTask(object sender,DrawItemEventArgs e) {
   if(e.Index<0) return;
   bool selected=(e.State&DrawItemState.Selected)!=0;
   using(var back=new SolidBrush(selected?Color.FromArgb(225,235,251):Color.White)) e.Graphics.FillRectangle(back,e.Bounds);
   if(selected) using(var bar=new SolidBrush(Color.FromArgb(35,100,210))) e.Graphics.FillRectangle(bar,e.Bounds.X,e.Bounds.Y,4,e.Bounds.Height);
   using(var font=new Font("Segoe UI",10.5f,selected?FontStyle.Bold:FontStyle.Regular))
   TextRenderer.DrawText(e.Graphics,tasks.Items[e.Index].ToString(),font,new Rectangle(e.Bounds.X+14,e.Bounds.Y,e.Bounds.Width-14,e.Bounds.Height),Color.FromArgb(30,30,30),TextFormatFlags.VerticalCenter|TextFormatFlags.Left|TextFormatFlags.EndEllipsis);
  }

  // ---------- selection ----------
  Job Current() { return tasks.SelectedIndex==main.Length-1 ? extra[Math.Max(0,advanced.SelectedIndex)] : main[Math.Max(0,tasks.SelectedIndex)]; }
  internal void SelectTask(int index) { tasks.SelectedIndex=index; }
  internal void SelectAdvanced(int index) { advanced.SelectedIndex=index; }
  internal void Shot(string path) { using(var bitmap = new Bitmap(Width,Height)) { DrawToBitmap(bitmap,new Rectangle(0,0,bitmap.Width,bitmap.Height)); bitmap.Save(path); } }
  void ShowTask() {
   if(tasks.SelectedIndex<0) return;
   bool isAdvanced=tasks.SelectedIndex==main.Length-1;
   Job job=Current();
   title.Text=isAdvanced?"Дополнительно":job.Title;
   description.Text=job.Description;
   advanced.Visible=isAdvanced;
   prepare.Visible=job.Prepare;
   beam.Visible=job.Beam;
   remote.Visible=remoteNote.Visible=job.Remote;
   start.Text=job.RunText;
   backupRow.Visible=job.BackupFile!=null;
   if(job.BackupFile!=null) { backupPath=FindNewest(Path.Combine(bundle,"runs"),job.BackupFile)??""; ShowBackup(); }
   if(!running) SetBanner("info","Выберите действие и нажмите кнопку. Пока ничего не менялось.");
  }
  void ShowBackup() {
   Job job=Current();
   if(String.IsNullOrEmpty(backupPath)) { backupLabel.Text="Резервная копия "+job.BackupName+" не найдена в kit\\runs. Эта операция доступна только на том компьютере, где выполнялась установка."; backupLabel.ForeColor=Color.Firebrick; }
   else { backupLabel.Text="Резервная копия: "+DescribeBackup(backupPath); backupLabel.ForeColor=Color.FromArgb(30,30,30); }
  }

  // ---------- backups ----------
  public static string FindNewest(string runs,string file) {
   if(!Directory.Exists(runs)) return null;
   var dirs=new List<string>(Directory.GetDirectories(runs)); dirs.Sort(StringComparer.Ordinal); dirs.Reverse();
   foreach(string d in dirs) if(File.Exists(Path.Combine(d,file))) return d;
   return null;
  }
  static string DescribeBackup(string path) {
   string name=Path.GetFileName(path); var m=Regex.Match(name,@"^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})");
   return m.Success ? m.Groups[3].Value+"."+m.Groups[2].Value+"."+m.Groups[1].Value+" "+m.Groups[4].Value+":"+m.Groups[5].Value+" ("+name+")" : name;
  }
  public static bool SelfTestBackups() {
   string dir=Path.Combine(Path.GetTempPath(),"xgimi-ui-"+Guid.NewGuid().ToString("N"));
   try {
    Directory.CreateDirectory(Path.Combine(dir,"20261001-100000-aaaaaa")); Directory.CreateDirectory(Path.Combine(dir,"20261013-120000-bbbbbb")); Directory.CreateDirectory(Path.Combine(dir,"20261014-090000-cccccc"));
    File.WriteAllText(Path.Combine(dir,"20261001-100000-aaaaaa","setup.json"),"{}"); File.WriteAllText(Path.Combine(dir,"20261013-120000-bbbbbb","setup.json"),"{}");
    return FindNewest(dir,"setup.json")==Path.Combine(dir,"20261013-120000-bbbbbb") && FindNewest(dir,"preparation.json")==null && FindNewest(Path.Combine(dir,"missing"),"setup.json")==null
     && DescribeBackup("20261013-120000-bbbbbb").StartsWith("13.10.2026 12:00");
   } finally { try { Directory.Delete(dir,true); } catch(Exception) {} }
  }
  internal bool CheckDescriptions() {
   if(main.Length!=5 || extra.Length!=10) return false;
   for(int i=0;i<main.Length;i++) {tasks.SelectedIndex=i; if(String.IsNullOrWhiteSpace(description.Text)||String.IsNullOrWhiteSpace(start.Text)||String.IsNullOrWhiteSpace(title.Text)) return false;}
   for(int i=0;i<extra.Length;i++) {tasks.SelectedIndex=main.Length-1; advanced.SelectedIndex=i; if(!description.Text.Contains(extra[i].Description)||String.IsNullOrWhiteSpace(start.Text)) return false;}
   tasks.SelectedIndex=0; return true;
  }

  // ---------- helpers ----------
  void SetBanner(string kind,string text) {
   banner.Text=text;
   switch(kind) {
    case "ok": banner.BackColor=Color.FromArgb(220,242,226); banner.ForeColor=Color.FromArgb(20,100,50); break;
    case "warn": banner.BackColor=Color.FromArgb(255,243,205); banner.ForeColor=Color.FromArgb(120,80,0); break;
    case "error": banner.BackColor=Color.FromArgb(251,225,225); banner.ForeColor=Color.FromArgb(150,30,30); break;
    default: banner.BackColor=Color.FromArgb(232,236,242); banner.ForeColor=Color.FromArgb(50,60,80); break;
   }
  }
  void SetLogVisible(bool visible) { log.Visible=visible; toggleLog.Text=visible?"Подробности ▴":"Подробности ▾"; }
  void Open(string path) {try {if(!File.Exists(path)&&!Directory.Exists(path)) {MessageBox.Show("Пока нет файлов: "+path,Text);return;} Process.Start(new ProcessStartInfo(path){UseShellExecute=true});}catch(Exception e){MessageBox.Show(e.Message,Text);}}
  public static string Address(string input) {
   input=input.Trim(); if(!Regex.IsMatch(input,@"^[A-Za-z0-9][A-Za-z0-9_.-]*(?::[0-9]{1,5})?$")) throw new ArgumentException("Введите IP или имя проектора, например 192.168.1.50 или 192.168.1.50:5555.");
   var parts=input.Split(':'); int port=5555; if(parts.Length==2 && (!Int32.TryParse(parts[1],out port)||port<1||port>65535)) throw new ArgumentException("Порт должен быть от 1 до 65535.");
   return parts[0]+":"+port;
  }
  public static string Quote(string value) {
   var result=new StringBuilder("\""); int slashes=0;
   foreach(char c in value) {
    if(c=='\\') {slashes++;continue;}
    if(c=='"') result.Append('\\',slashes*2+1); else result.Append('\\',slashes);
    result.Append(c);slashes=0;
   }
   result.Append('\\',slashes*2);result.Append('"');return result.ToString();
  }
  void Append(string text) {if(String.IsNullOrEmpty(text)||IsDisposed)return; if(InvokeRequired){BeginInvoke(new Action<string>(Append),text);return;} log.AppendText(text+Environment.NewLine);}
  string SettingsFile { get { return Path.Combine(bundle,"ui-settings.txt"); } }
  void LoadSettings() { try { if(File.Exists(SettingsFile)) ip.Text=File.ReadAllText(SettingsFile,Encoding.UTF8).Trim(); } catch(Exception) {} }
  void SaveSettings() { try { if(Directory.Exists(bundle)) File.WriteAllText(SettingsFile,ip.Text.Trim(),Encoding.UTF8); } catch(Exception) {} }
  static string Reason(string output) {
   string last=""; foreach(string raw in output.Split('\n')) { string line=raw.Trim(); if(line.Length==0) continue; if(line.StartsWith("ОШИБКА",StringComparison.OrdinalIgnoreCase)||line.StartsWith("Ошибка")) return line; last=line; }
   return last;
  }

  async Task<List<string>> PickLaunchers(string address,string directory) {
   string output=Path.Combine(directory,Guid.NewGuid().ToString("N")+"-launchers.json");
   var info=new ProcessStartInfo(Path.Combine(bundle,"runtime","python.exe"),"-I -u "+Quote(Path.Combine(bundle,"launch.py"))+" list-launchers --device "+Quote(address)+" --output "+Quote(output)) {WorkingDirectory=bundle,UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8};
   using(var process=new Process {StartInfo=info}) {
    process.Start();var stdout=process.StandardOutput.ReadToEndAsync();var stderr=process.StandardError.ReadToEndAsync();await Task.Run(()=>process.WaitForExit());
    string text=await stdout;string errors=await stderr;
    if(process.ExitCode!=0)throw new Exception("Не удалось проверить лаунчеры: "+text+errors);
   }
   var data=(Dictionary<string,object>)new JavaScriptSerializer().DeserializeObject(File.ReadAllText(output,Encoding.UTF8));
   var items=(object[])data["launchers"];var selected=new List<string>();
   if(items.Length==0){Append("Других активных лаунчеров не найдено.");return selected;}
   using(var dialog=new Form {Text="Другие домашние экраны",Size=new Size(650,400),StartPosition=FormStartPosition.CenterParent,Font=Font,MinimizeBox=false,MaximizeBox=false}) {
    var note=new Label {Text="Выберите лаунчеры, которые нужно отключить. Неотмеченные останутся включёнными. Состояния сохранятся для возврата. Штатный XGIMI отключается отдельно после назначения BEAM; FallbackHome сохраняется.",Dock=DockStyle.Top,Height=90,Padding=new Padding(12)};
    var list=new CheckedListBox {Dock=DockStyle.Fill,CheckOnClick=true};foreach(object item in items)list.Items.Add((string)item,false);
    var buttons=new FlowLayoutPanel {Dock=DockStyle.Bottom,Height=48,FlowDirection=FlowDirection.RightToLeft};
    var cancel=new Button {Text="Отмена",DialogResult=DialogResult.Cancel,Width=110};var ok=new Button {Text="Продолжить",DialogResult=DialogResult.OK,Width=130};buttons.Controls.Add(cancel);buttons.Controls.Add(ok);
    dialog.Controls.Add(list);dialog.Controls.Add(note);dialog.Controls.Add(buttons);dialog.AcceptButton=ok;dialog.CancelButton=cancel;
    if(dialog.ShowDialog(this)!=DialogResult.OK)throw new OperationCanceledException("Отменено до изменений проектора.");
    foreach(object item in list.CheckedItems)selected.Add((string)item);
   }
   return selected;
  }

  /// <summary>Starts launch.py, mirrors its output into the log and returns the exit code and the full output.</summary>
  async Task<KeyValuePair<int,string>> RunLaunch(string args) {
   var info=new ProcessStartInfo(Path.Combine(bundle,"runtime","python.exe"),args) {WorkingDirectory=bundle,UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8};
   var output=new StringBuilder(); object sync=new object();
   using(var process=new Process {StartInfo=info}) {
    DataReceivedEventHandler received=delegate(object sender,DataReceivedEventArgs e){if(e.Data!=null){lock(sync){output.AppendLine(e.Data);} Append(e.Data);}};
    process.OutputDataReceived+=received;process.ErrorDataReceived+=received;
    process.Start();process.BeginOutputReadLine();process.BeginErrorReadLine();
    await Task.Run(()=>process.WaitForExit());
    return new KeyValuePair<int,string>(process.ExitCode,output.ToString());
   }
  }

  void Lock(bool locked) {
   running=locked; start.Enabled=!locked; tasks.Enabled=!locked; advanced.Enabled=!locked; ip.Enabled=!locked; backupBrowse.Enabled=!locked;
   timezone.Enabled=services.Enabled=beam.Enabled=remote.Enabled=!locked;
   progress.Style=locked?ProgressBarStyle.Marquee:ProgressBarStyle.Blocks;
  }

  async Task Execute() {
   if(running) return;
   Job job=Current(); string address;
   try {
    address=Address(ip.Text);
    if(!File.Exists(Path.Combine(bundle,"runtime","python.exe"))||!File.Exists(Path.Combine(bundle,"launch.py"))) throw new Exception("Папка kit отсутствует или неполная. Распакуйте весь комплект рядом с EXE.");
    if(job.BackupFile!=null) {
     if(String.IsNullOrWhiteSpace(backupPath)||!File.Exists(Path.Combine(backupPath,job.BackupFile))) throw new Exception("Не найдена резервная копия "+job.BackupName+" (файл "+job.BackupFile+" в kit\\runs). Выберите папку вручную кнопкой «Другая…».");
    }
   } catch(Exception e) { MessageBox.Show(e.Message,Text,MessageBoxButtons.OK,MessageBoxIcon.Information); return; }
   string confirm=ConfirmText(job);
   if(confirm!=null && MessageBox.Show(confirm,job.Title,MessageBoxButtons.YesNo,MessageBoxIcon.Question)!=DialogResult.Yes) return;
   SaveSettings();
   Lock(true); log.Clear(); SetLogVisible(false);
   SetBanner("info","Выполняется: "+job.Title+"… Не закрывайте окно и не выключайте проектор.");
   string session=Path.Combine(bundle,"ui-logs"); string transcript=Path.Combine(session,DateTime.Now.ToString("yyyyMMdd-HHmmss")+"-"+Guid.NewGuid().ToString("N")+".log");
   try {
    Directory.CreateDirectory(session);
    string args="-I -u "+Quote(Path.Combine(bundle,"launch.py"))+" "+job.Command+" --device "+Quote(address);
    if(job.BackupFile!=null) args+=" --backup "+Quote(backupPath);
    if(job.Plan) args+=" --plan";
    if(job.Prepare) {
     if(timezone.SelectedIndex>0) args+=" --timezone "+Quote(zones[timezone.SelectedIndex]);
     if(services.Checked) args+=" --disable-services";
     if(job.Beam&&beam.Checked) {
      args+=" --install-beam";
      if(!job.Plan) foreach(string package in await PickLaunchers(address,session)) args+=" --disable-launcher "+Quote(package);
     }
    }
    var run=await RunLaunch(args); int code=run.Key; string text=run.Value;
    string finalCommand=job.Command;
    // The installer refuses a first installation over an existing one: offer the update instead of a dead end.
    if(code!=0 && job.Command=="prepare-install" && text.Contains("Русификатор уже установлен")) {
     bool extras=timezone.SelectedIndex>0||services.Checked||beam.Checked;
     if(MessageBox.Show("Русификатор уже установлен на этом проекторе.\r\n\r\nОбновить его до версии из этого комплекта?"+(extras?"\r\n\r\nПри обновлении язык, часовой пояс, отключение сервисов и BEAM не применяются; их можно выполнить отдельно в «Дополнительно».":""),"Уже установлено",MessageBoxButtons.YesNo,MessageBoxIcon.Question)==DialogResult.Yes) {
      Append(""); Append("— Обновление установленного русификатора —");
      run=await RunLaunch("-I -u "+Quote(Path.Combine(bundle,"launch.py"))+" update-boot --device "+Quote(address)); code=run.Key; text+=run.Value; finalCommand="update-boot";
     }
    }
    // Everything chosen on the install page is done from one run: the remote-buttons module follows the translation.
    int remoteCode=-1; string remoteText="";
    if(code==0 && job.Remote && remote.Checked) {
     Append(""); Append("— Модуль кнопок пульта —"); SetBanner("info","Выполняется: установка модуля кнопок пульта…");
     var second=await RunLaunch("-I -u "+Quote(Path.Combine(bundle,"launch.py"))+" install-remote --device "+Quote(address)); remoteCode=second.Key; remoteText=second.Value; text+=remoteText;
    }
    // A first installation is completed with a reboot: until XGIMI's memory rules are loaded (at boot) the system
    // switches the autostart services of fresh packages off within seconds, so they are switched on again afterwards.
    int finishCode=-1; string finishText="";
    if(code==0 && (finalCommand=="prepare-install"||finalCommand=="install-remote"||remoteCode==0)) {
     Append(""); Append("— Завершение настройки: перезагрузка проектора —");
     SetBanner("info","Перезагрузка проектора и завершение настройки: 2–4 минуты. Не выключайте проектор и не закрывайте окно.");
     var third=await RunLaunch("-I -u "+Quote(Path.Combine(bundle,"launch.py"))+" finish-setup --device "+Quote(address)); finishCode=third.Key; finishText=third.Value; text+=finishText;
    }
    File.WriteAllText(transcript,text,Encoding.UTF8);
    Append("Журнал интерфейса: "+transcript);
    Report(finalCommand,code,text,remoteCode,remoteText,finishCode,finishText);
   } catch(OperationCanceledException e) { Append(e.Message); SetBanner("warn","Отменено до изменений. Проектор не менялся."); }
   catch(Exception e) { Append("Ошибка: "+e.Message); SetBanner("error","Не удалось запустить операцию: "+e.Message); SetLogVisible(true); }
   finally { Lock(false); }
  }

  string ConfirmText(Job job) {
   if(job.Command=="prepare-install") {
    var sb=new StringBuilder("Будет выполнено:\r\n\r\n• включён русский язык и созданы нужные базы данных;\r\n• установлен перевод с автозапуском;\r\n");
    sb.Append(timezone.SelectedIndex>0?"• часовой пояс: "+zoneNames[timezone.SelectedIndex]+";\r\n":"• часовой пояс не меняется;\r\n");
    if(services.Checked) sb.Append("• отключены фоновые китайские сервисы XGIMI;\r\n");
    if(beam.Checked) sb.Append("• установлен лаунчер BEAM (понадобится интернет на компьютере);\r\n");
    if(remote.Checked) sb.Append("• установлен модуль кнопок пульта;\r\n");
    sb.Append("• в конце проектор будет перезагружен автоматически (2–4 минуты), и настройка завершится сама.\r\n");
    sb.Append("\r\nПеред изменениями создаются резервные копии. Продолжить?");
    return sb.ToString();
   }
   if(job.Command=="install-remote") return "Установить модуль кнопок пульта?\r\n\r\nВ конце проектор будет перезагружен автоматически (2–4 минуты), чтобы служба кнопок включилась окончательно.";
   if(job.Command=="finish-setup") return "Перезагрузить проектор и завершить настройку?\r\n\r\nЭто займёт 2–4 минуты. Проектор перезагрузится сам; если он останется выключенным, включите его с пульта.";
   if(job.Command=="remove-autostart") return "Удалить русификацию с проектора?\r\n\r\nПосле перезагрузки интерфейс снова будет на китайском. Данные будут возвращены из резервной копии:\r\n"+DescribeBackup(backupPath);
   if(job.Command=="prepare" && !job.Plan) return "Подготовить проектор?\r\n\r\nБудут включены русский язык"+(timezone.SelectedIndex>0?", часовой пояс «"+zoneNames[timezone.SelectedIndex]+"»":"")+(services.Checked?", отключены китайские сервисы":"")+(beam.Checked?" и установлен BEAM":"")+". Изменения можно отменить в «Дополнительно».";
   return null;
  }

  /// <summary>Turns the exit code into a result a person can act on.</summary>
  void Report(string command,int code,string output,int remoteCode,string remoteText,int finishCode,string finishText) {
   if(code==0) {
    if(finishCode>0) {
     SetBanner("warn","Установка выполнена, но завершить настройку не удалось: "+Reason(finishText)+" Если проектор выключен, включите его с пульта и запустите «Дополнительно → Завершить настройку»."); SetLogVisible(true); return;
    }
    if((command=="prepare-install"||command=="update-boot") && remoteCode>0) {
     SetBanner("warn",(command=="update-boot"?"Русификатор обновлён":"Русификация установлена")+", но модуль кнопок пульта не поставился: "+Reason(remoteText)+" Повторите его установку: Дополнительно → «Кнопки пульта: установить или обновить»."); SetLogVisible(true); return;
    }
    string rebooted=finishCode==0?" Проектор уже перезагружен, перевод применён: проверьте его.":"";
    string buttons=remoteCode==0?" Модуль кнопок включён: назначьте действия в Настройки → Общее → Кнопки пульта.":"";
    switch(command) {
     case "check": SetBanner("ok","Проверка пройдена: проектор подключён и совместим с русификатором. Ничего не менялось."); SetLogVisible(true); break;
     case "prepare-install": SetBanner("ok","Русификация установлена."+rebooted+buttons); break;
     case "update-boot": SetBanner("ok","Русификатор обновлён. Если перевод не изменился, перезагрузите проектор."+(remoteCode==0?rebooted:"")+buttons); break;
     case "remove-autostart": SetBanner("ok","Русификация удалена. Перезагрузите проектор — интерфейс вернётся к прежнему виду."); break;
     case "recover-autostart": SetBanner("ok","Состояние восстановлено. Перезагрузите проектор."); break;
     case "finish-setup": SetBanner("ok","Настройка завершена: службы включены и держатся, перевод применён. Дальнейшие перезагрузки не требуют действий."); break;
     case "install-remote": SetBanner("ok","Модуль кнопок установлен и включён (проектор перезагружен). Назначьте действия: Настройки → Общее → Кнопки пульта."); break;
     case "enable-remote": SetBanner("ok","Готово. Назначьте действия кнопкам: Настройки → Общее → Кнопки пульта."); break;
     default: SetBanner("ok",Current().Plan?"Готово: текущее состояние показано в подробностях ниже. Ничего не менялось.":"Готово."); if(Current().Plan) SetLogVisible(true); break;
    }
    return;
   }
   if(code==10 && (command=="prepare-install"||command=="prepare")) { SetBanner("warn","Язык изменён. Перезагрузите проектор и запустите этот же пункт ещё раз — установка продолжится."); return; }
   SetBanner("error","Не получилось. "+Reason(output)+"  Подробности ниже; проектор не будет повреждён — после исправления причины можно повторить."); SetLogVisible(true);
  }
 }
}

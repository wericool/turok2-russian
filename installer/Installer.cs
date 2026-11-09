// Установщик русификатора Turok 2: Seeds of Evil Remastered (3.0.x).
// Собирается стандартным csc.exe из .NET Framework 4 (C# 5), см. build_installer.cmd.
// Внутрь встраивается dist\Siberian.kpf; установка = копирование в <игра>\mods\Siberian.kpf.
using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Turok 2 Russian")]
[assembly: AssemblyDescription("Русификатор Turok 2: Seeds of Evil Remastered 3.0")]
[assembly: AssemblyProduct("Turok 2 Russian")]
[assembly: AssemblyCompany("Siberian Studio (2018), ericool (2026)")]
[assembly: AssemblyCopyright("Основа: русификатор Siberian Studio (2018). Перевод новых текстов, адаптация под 3.0 и исправления: ericool (2026)")]
[assembly: AssemblyVersion("2026.11.9.0")]

static class Program
{
    const string GameDirName = "Turok 2 - Seeds of Evil";
    const string ModName = "Siberian.kpf";

    [STAThread]
    static void Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        string path = args.Length > 0 ? args[0] : FindGame();
        Application.Run(new SetupForm(path ?? ""));
    }

    public static string FindGame()
    {
        foreach (string lib in SteamLibraries())
        {
            string p = Path.Combine(Path.Combine(Path.Combine(lib, "steamapps"), "common"), GameDirName);
            if (IsGameDir(p)) return p;
        }
        return null;
    }

    static System.Collections.Generic.List<string> SteamLibraries()
    {
        var roots = new System.Collections.Generic.List<string>();
        AddReg(roots, Registry.CurrentUser, @"Software\Valve\Steam", "SteamPath");
        AddReg(roots, Registry.LocalMachine, @"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath");
        AddReg(roots, Registry.LocalMachine, @"SOFTWARE\Valve\Steam", "InstallPath");
        var libs = new System.Collections.Generic.List<string>();
        foreach (string r0 in roots)
        {
            string r = r0.Replace('/', '\\');
            if (!libs.Contains(r)) libs.Add(r);
            try
            {
                string vdf = Path.Combine(Path.Combine(r, "steamapps"), "libraryfolders.vdf");
                if (!File.Exists(vdf)) continue;
                foreach (Match m in Regex.Matches(File.ReadAllText(vdf), "\"path\"\\s+\"([^\"]+)\""))
                {
                    string p = m.Groups[1].Value.Replace("\\\\", "\\");
                    if (!libs.Contains(p)) libs.Add(p);
                }
            }
            catch { }
        }
        return libs;
    }

    static void AddReg(System.Collections.Generic.List<string> list, RegistryKey hive, string key, string name)
    {
        try
        {
            using (RegistryKey k = hive.OpenSubKey(key))
            {
                if (k == null) return;
                string v = k.GetValue(name) as string;
                if (!string.IsNullOrEmpty(v)) list.Add(v);
            }
        }
        catch { }
    }

    public static bool IsGameDir(string p)
    {
        return !string.IsNullOrEmpty(p) && File.Exists(Path.Combine(p, "game.kpf")) && File.Exists(Path.Combine(p, "Turok2.exe"));
    }

    public static byte[] ModBytes()
    {
        using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream(ModName))
        using (MemoryStream ms = new MemoryStream())
        {
            s.CopyTo(ms);
            return ms.ToArray();
        }
    }

    public static string ModPath(string game)
    {
        return Path.Combine(Path.Combine(game, "mods"), ModName);
    }
}

class SetupForm : Form
{
    TextBox pathBox = new TextBox();
    Label status = new Label();

    public SetupForm(string path)
    {
        Text = "Turok 2: Seeds of Evil — русификатор";
        Font = new Font("Segoe UI", 9.5f);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(600, 334);
        try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

        var title = new Label();
        title.Text = "Русификатор Turok 2: Seeds of Evil Remastered";
        title.Font = new Font("Segoe UI", 13f, FontStyle.Bold);
        title.SetBounds(16, 12, 570, 28);
        Controls.Add(title);

        var info = new Label();
        info.Text = "Для версии игры 3.0.x (Steam). Перевод интерфейса, предметов, заданий, субтитров роликов,\n" +
                    "достижений и настроек; шрифты с кириллицей.";
        info.SetBounds(16, 44, 570, 40);
        Controls.Add(info);

        var credits = new GroupBox();
        credits.Text = "Авторы";
        credits.SetBounds(16, 88, 568, 62);
        var credText = new Label();
        credText.Text = "За основу взят русификатор Siberian Studio (2018).\n" +
                        "Перевод новых текстов, адаптация под версию 3.0 и исправления — ericool.";
        credText.SetBounds(10, 18, 550, 38);
        credits.Controls.Add(credText);
        Controls.Add(credits);

        var lbl = new Label();
        lbl.Text = "Папка игры:";
        lbl.SetBounds(16, 162, 570, 20);
        Controls.Add(lbl);

        pathBox.Text = path;
        pathBox.SetBounds(16, 184, 470, 26);
        pathBox.TextChanged += delegate { UpdateStatus(); };
        Controls.Add(pathBox);

        var browse = new Button();
        browse.Text = "Обзор…";
        browse.SetBounds(494, 182, 90, 28);
        browse.Click += delegate
        {
            using (var d = new FolderBrowserDialog())
            {
                d.Description = "Выберите папку «" + "Turok 2 - Seeds of Evil" + "» (где лежит game.kpf)";
                if (Directory.Exists(pathBox.Text)) d.SelectedPath = pathBox.Text;
                if (d.ShowDialog(this) == DialogResult.OK) pathBox.Text = d.SelectedPath;
            }
        };
        Controls.Add(browse);

        status.SetBounds(16, 218, 570, 60);
        Controls.Add(status);

        var install = new Button();
        install.Text = "Установить";
        install.SetBounds(16, 288, 140, 32);
        install.Click += delegate { DoInstall(); };
        Controls.Add(install);
        AcceptButton = install;

        var remove = new Button();
        remove.Text = "Удалить";
        remove.SetBounds(164, 288, 120, 32);
        remove.Click += delegate { DoRemove(); };
        Controls.Add(remove);

        var exit = new Button();
        exit.Text = "Выход";
        exit.SetBounds(484, 288, 100, 32);
        exit.Click += delegate { Close(); };
        Controls.Add(exit);
        CancelButton = exit;

        UpdateStatus();
    }

    string Game { get { return pathBox.Text.Trim().Trim('"'); } }

    void UpdateStatus()
    {
        string g = Game;
        if (!Program.IsGameDir(g))
        {
            status.ForeColor = Color.Firebrick;
            status.Text = g.Length == 0 ? "Игра не найдена автоматически. Укажите папку через «Обзор…»."
                                        : "В этой папке нет Turok2.exe и game.kpf.";
            return;
        }
        status.ForeColor = SystemColors.ControlText;
        string s = File.Exists(Program.ModPath(g)) ? "Сейчас в игре уже стоит Siberian.kpf (будет заменён)." : "Русификатор ещё не установлен.";
        string ver = GameVersion(g);
        if (ver != null && !ver.StartsWith("3."))
            s += "\nВнимание: найдена версия игры " + ver + ", русификатор рассчитан на 3.0.x.";
        if (Directory.Exists(Path.Combine(g, "SibTextUninst")))
            s += "\nНайден деинсталлятор старого русификатора (SibTextUninst) — не запускайте его, он удалит этот перевод.";
        status.Text = s;
    }

    static string GameVersion(string g)
    {
        try
        {
            string cl = Path.Combine(g, "changelog.txt");
            if (!File.Exists(cl)) return null;
            Match m = Regex.Match(File.ReadAllText(cl), @"^\s*([\d.]+)\s+Patch Notes", RegexOptions.Multiline);
            return m.Success ? m.Groups[1].Value : null;
        }
        catch { return null; }
    }

    bool GameRunning()
    {
        if (Process.GetProcessesByName("Turok2").Length == 0) return false;
        MessageBox.Show(this, "Закройте игру и повторите.", Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
        return true;
    }

    void DoInstall()
    {
        string g = Game;
        if (!Program.IsGameDir(g)) { UpdateStatus(); return; }
        if (GameRunning()) return;
        try
        {
            Directory.CreateDirectory(Path.Combine(g, "mods"));
            File.WriteAllBytes(Program.ModPath(g), Program.ModBytes());
        }
        catch (UnauthorizedAccessException) { Elevate(g); return; }
        catch (Exception e) { MessageBox.Show(this, "Ошибка: " + e.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
        UpdateStatus();
        MessageBox.Show(this,
            "Русификатор установлен:\n" + Program.ModPath(g) +
            "\n\nВ игре должен быть выбран английский язык (English) — перевод заменяет именно его.",
            Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    void DoRemove()
    {
        string g = Game;
        if (!Program.IsGameDir(g)) { UpdateStatus(); return; }
        if (GameRunning()) return;
        string mod = Program.ModPath(g);
        if (!File.Exists(mod))
        {
            MessageBox.Show(this, "Русификатор не установлен.", Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        try
        {
            File.Delete(mod);
            string mods = Path.Combine(g, "mods");
            if (Directory.GetFileSystemEntries(mods).Length == 0) Directory.Delete(mods);
        }
        catch (UnauthorizedAccessException) { Elevate(g); return; }
        catch (Exception e) { MessageBox.Show(this, "Ошибка: " + e.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Error); return; }
        UpdateStatus();
        MessageBox.Show(this, "Русификатор удалён. Файлы игры не изменялись.", Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    void Elevate(string g)
    {
        if (MessageBox.Show(this, "Нет доступа к папке игры. Перезапустить установщик от имени администратора?",
                            Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        try
        {
            var psi = new ProcessStartInfo(Application.ExecutablePath, "\"" + g + "\"");
            psi.Verb = "runas";
            psi.UseShellExecute = true;
            Process.Start(psi);
            Close();
        }
        catch { }
    }
}

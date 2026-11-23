using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;

namespace PyCalphadSuite.Desktop;

/// <summary>
/// Interaction logic for App.xaml with comprehensive crash prevention and logging.
/// </summary>
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // Global UI Dispatcher Exception Trapping - Prevents any UI crash
        DispatcherUnhandledException += OnDispatcherUnhandledException;

        // Global AppDomain Exception Trapping
        AppDomain.CurrentDomain.UnhandledException += OnAppDomainUnhandledException;

        // Global Task Exception Trapping - Prevents async task background crashes
        TaskScheduler.UnobservedTaskException += OnUnobservedTaskException;

        string? startupCompPath = null;
        foreach (var arg in e.Args)
        {
            if (string.IsNullOrWhiteSpace(arg)) continue;
            var candidate = arg.Trim().Trim('"');
            if (File.Exists(candidate))
            {
                var ext = Path.GetExtension(candidate).ToLowerInvariant();
                if (ext is ".json" or ".csv" or ".dat")
                {
                    startupCompPath = candidate;
                    break;
                }
            }
        }

        try
        {
            var win = new MainWindow(startupCompPath);
            MainWindow = win;
            win.Show();
        }
        catch (Exception ex)
        {
            LogCrash("Startup Exception", ex);
            MessageBox.Show(
                $"Failed to start CALPHAD XOC:\n{ex.Message}\n\nCheck csharp_crash_log.txt for details.",
                "CALPHAD XOC - Startup Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }

    private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        LogCrash("Dispatcher Unhandled Exception", e.Exception);
        try
        {
            MessageBox.Show(
                $"A handled exception occurred:\n{e.Exception.Message}\n\nThe operation was safely recovered and logged. CALPHAD XOC will keep running.",
                "CALPHAD XOC - Handled Exception",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }
        catch { }

        e.Handled = true; // Mark as handled to prevent application crash
    }

    private void OnAppDomainUnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        if (e.ExceptionObject is Exception ex)
        {
            LogCrash("AppDomain Unhandled Exception", ex);
        }
        else
        {
            LogCrash("AppDomain Unhandled Exception", new Exception(e.ExceptionObject?.ToString() ?? "Unknown error"));
        }
    }

    private void OnUnobservedTaskException(object? sender, UnobservedTaskExceptionEventArgs e)
    {
        LogCrash("Unobserved Task Exception", e.Exception);
        e.SetObserved(); // Mark as observed to prevent process termination
    }

    private static void LogCrash(string category, Exception ex)
    {
        try
        {
            string logDir = AppDomain.CurrentDomain.BaseDirectory;
            string logPath = Path.Combine(logDir, "csharp_crash_log.txt");
            string text = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] [{category}]\n{ex}\n--------------------------------------------------------------------------------\n";
            File.AppendAllText(logPath, text);
        }
        catch { }
    }
}

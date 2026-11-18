// SPDX-License-Identifier: GPL-2.0-or-later
#include <QCoreApplication>
#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLibrary>
#include <QPluginLoader>
#include <QTextStream>

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    const QStringList args = app.arguments();
    if (args.size() != 4) {
        QTextStream(stderr) << "Usage: " << args.value(0)
                            << " <plugin.so> <resource_prefix> <output_dir>\n";
        return 2;
    }

    const QString pluginPath = args.at(1);
    QString prefix = args.at(2);
    if (!prefix.endsWith(QLatin1Char('/'))) {
        prefix.append(QLatin1Char('/'));
    }
    const QDir outDir(args.at(3));

    QLibrary lib(pluginPath);
    if (!lib.load()) {
        QTextStream(stderr) << "Failed to load plugin " << pluginPath << ": "
                            << lib.errorString() << "\n";
        return 1;
    }

    QDirIterator it(prefix, QDir::Files, QDirIterator::Subdirectories);
    int count = 0;
    while (it.hasNext()) {
        const QString src = it.next();
        const QString rel = src.mid(prefix.size());
        QFile inFile(src);
        if (!inFile.open(QIODevice::ReadOnly)) {
            QTextStream(stderr) << "Failed to open resource " << src << "\n";
            return 1;
        }
        const QString destPath = outDir.filePath(rel);
        QDir().mkpath(QFileInfo(destPath).path());
        QFile outFile(destPath);
        if (!outFile.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
            QTextStream(stderr) << "Failed to write " << destPath << "\n";
            return 1;
        }
        outFile.write(inFile.readAll());
        ++count;
    }

    if (count == 0) {
        QTextStream(stderr) << "No resources found under " << prefix << " in " << pluginPath << "\n";
        return 1;
    }

    QPluginLoader loader(pluginPath);
    const QJsonObject meta = loader.metaData().value(QStringLiteral("MetaData")).toObject();
    if (!meta.isEmpty()) {
        QFile metaFile(outDir.filePath(QStringLiteral("_plugin_metadata.json")));
        if (!metaFile.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
            QTextStream(stderr) << "Failed to write _plugin_metadata.json\n";
            return 1;
        }
        metaFile.write(QJsonDocument(meta).toJson(QJsonDocument::Indented));
    }

    // Do not call lib.unload(); Qt resource/type unregistration on exit can crash.
    return 0;
}

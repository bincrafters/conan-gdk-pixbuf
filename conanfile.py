from conans import ConanFile, Meson, tools
from conans.errors import ConanInvalidConfiguration
import os
import shutil


class LibnameConan(ConanFile):
    name = "gdk-pixbuf"
    description = "toolkit for image loading and pixel buffer manipulation"
    topics = ("conan", "gdk-pixbuf", "image")
    url = "https://github.com/bincrafters/conan-gdk-pixbuf"
    homepage = "https://developer.gnome.org/gdk-pixbuf/"
    license = "LGPL-2.1"
    generators = "pkg_config"

    # Options may need to change depending on the packaged library
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libpng": [True, False],
        "with_libtiff": [True, False],
        "with_libjpeg": [True, False],
        "with_jasper": [True, False],
        }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libpng": True,
        "with_libtiff": True,
        "with_libjpeg": True,
        "with_jasper": False,
        }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
    
    def build_requirements(self):
        self.build_requires('meson/0.53.0')
        if not tools.which('pkg-config'):
            self.build_requires('pkg-config_installer/0.29.2@bincrafters/stable')
    
    def system_requirements(self):
        if self.settings.os == 'Linux':
            installer = tools.SystemPackageTool()
            installer.install("shared-mime-info")
    
    def requirements(self):
        self.requires('glib/2.58.3@bincrafters/stable')
        if self.options.with_libpng:
            self.requires('libpng/1.6.37')
        if self.options.with_libtiff:
            self.requires('libtiff/4.0.9')
        if self.options.with_libjpeg:
            self.requires('libjpeg/9d')
        if self.options.with_jasper:
            self.requires('jasper/2.0.14')

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)
        tools.replace_in_file(os.path.join(self._source_subfolder, 'meson.build'), "subdir('tests')", "#subdir('tests')")

    def _configure_meson(self):
        meson = Meson(self)
        defs = {}
        defs['gir'] = 'false'
        defs['docs'] = 'false'
        defs['man'] = 'false'
        defs['installed_tests'] = 'false'
        defs['png'] = 'true' if self.options.with_libpng else 'false'
        defs['tiff'] = 'true' if self.options.with_libtiff else 'false'
        defs['jpeg'] = 'true' if self.options.with_libjpeg else 'false'
        defs['jasper'] = 'true' if self.options.with_jasper else 'false'
        defs['x11'] = 'false'
        args=[]
        args.append('--wrap-mode=nofallback')
        meson.configure(defs=defs, build_folder=self._build_subfolder, source_folder=self._source_subfolder, pkg_config_paths='.', args=args)
        return meson

    def build(self):
        for package in self.deps_cpp_info.deps:
            lib_path = self.deps_cpp_info[package].rootpath
            for dirpath, _, filenames in os.walk(lib_path):
                for filename in filenames:
                    if filename.endswith('.pc'):
                        shutil.copyfile(os.path.join(dirpath, filename), filename)
                        tools.replace_prefix_in_pc_file(filename, lib_path)
        meson = self._configure_meson()
        meson.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        with tools.environment_append({'LD_LIBRARY_PATH': os.path.join(self.package_folder, 'lib')}):
            meson = self._configure_meson()
            meson.install()
        # If the CMakeLists.txt has a proper install method, the steps below may be redundant
        # If so, you can just remove the lines below
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs = ['include/gdk-pixbuf-2.0']
        self.cpp_info.names['pkg_config'] = 'gdk-pixbuf-2.0'
        if self.settings.os == 'Linux':
            self.cpp_info.system_libs = ['m']

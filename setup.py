# flake8: noqa
# encoding: utf-8
#
# A modifier: 
#        toute occurrence de "altictoh"/package_name 
#        packages=find_packages(exclude.....
#        install_requires
#        entry_points

from setuptools import setup, find_packages, Extension, find_namespace_packages
import sys, os
import numpy
import vcversioner

package_name='altis'

from setuptools.command.install import install

package_version=vcversioner.find_version(
        version_module_paths=['%s/_version.py' % package_name]).version
package_sha=vcversioner.find_version(
        version_module_paths=['%s/_version.py' % package_name]).sha

version = package_version+'_'+package_sha


class CustomInstall(install):
    def run(self):
        print("hello pre_install_message")
        install.run(self)
        print("post_install_message")

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name=package_name,
      version=version,
      description="Altimetry Times Series Software (AlTiS Software)",
      long_description=long_description,
      classifiers=[
                "Topic :: Scientific/Engineering :: Physics",
                "Intended Audience :: Science/Research",
                "Topic :: Scientific/Engineering :: Hydrology",
                "Development Status :: 4 - Beta",
                "Programming Language :: Python :: 3",
                "License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)",
                "Operating System :: Microsoft :: Windows",
                "Operating System :: POSIX :: Linux",
                "Operating System :: MacOS",
                ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='radar altimetry, time series, CTOH',
      author='CTOH',
      author_email='blarel@legos.obs-mip.fr, ctoh_products@legos.obs-mip.fr, altis@groupes.renater.fr',
      url='http://ctoh.legos.obs-mip.fr',
      license = 'CeCiLL-2.1',
      packages=find_namespace_packages('.',exclude=['tests']),
      
      package_data={package_name : ['HELP.txt'],
                            'etc' : ['*.yml','*.png','*.html'],
                            },
      include_package_data=False,
      zip_safe=False,
      setup_requires=['vcversioner'],
      vcversioner={'version_module_paths': ['%s/_version.py' % package_name]},
      #cmdclass={'install': CustomInstall},
      install_requires=[
#            "geopandas>=0.4.1",
#            "matplotlib>=3.0.3",
#            "netcdf4>=1.4.2"
#            "numpy>=1.16.3",
#            "owslib>=0.17.1",
#            "pandas>=0.24.2",
#            "shapely>=1.6.4",
#            "wxpython>=4.0.4",
#            "xarray>=0.12.1",
#            "yachain>=0.1.4",
          # -*- Extra requirements: -*-
      ],
      python_requires='>=3.7',
      entry_points={
          'console_scripts': [
               'altis_gui = %s.altis_gui:main' % package_name,
        ]
      },)




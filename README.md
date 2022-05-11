# Altimetry Time Series (AlTiS) Software

[[_TOC_]]


AlTiS is software developed by [CTOH](http://ctoh.legos.obs-mip.fr/) as part of its activities as a National Observation Service. Altis is free software and it is released as open source under the [CeCill License](LICENSE), and is available for download free of charge. Altis is working under python3 environment ([Anaconda distribution](https://www.anaconda.com)) and tested for GNU/Linux, Windows 10 (and soon for Mac OS X).
 
The AlTiS 1.4 (2020/11) has now identifier [IDDN.FR.010.0121234.000.R.X.2020.041.30000](https://www.iddn.org/cgi-iddn/certificat.cgi?IDDN.FR.010.0121234.000.R.X.2020.041.30000) IDDN Certification
 

### AlTiS software is developed for:
 - Research : Analysis tool allowing altimetry data studies over small area like rivers, lakes, flood areas in order to create water time series.
 - Training : Education tools to manipulate radar altimetry data and evaluate their potential to monitor water bodies.


## Install
The installation instruction is available [here](INSTALL.md)

## Altimetric Data
AlTiS accepts [CTOH](http://ctoh.legos.obs-mip.fr/) altimetry products (Level 2 GDR). CTOH data are GDR, specifically conditioned for optimized the data size by making a geographical selection and includes the right altimetry parameters for hydrological studies. 

### Data request
- For the altimetry data access, just fill the [request form](http://ctoh.legos.obs-mip.fr/applications/land_surfaces/altimatric_data/altis/altis).

The products are available for the altimetry missions below :

                     
| Mission |Product Name|	Cycles |          Dates           | Version / Product reference | Orbit Phase |
| ------- |	---------- | --------- | ------------------------ | --------------------------- | ----------- |
| Topex | tpx_a_cash_d_gdr | 10 - 359 | 1992/12/21 to 2002/06/22 |	CASH product (available soon) | [nominal Jason orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_RefOrbit_J3J2J1TP_Tracks_GoogleEarth_V3.kmz)|
| ERS-2   | ers2_a_ctoh_v0100_gdr |	1 - 89 | 1995/05/17 to 2003/11/24 |	CTOH product                | [nominal ERS orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_EN_Tracks_GE_OldOrbit.kmz) |
| ENVISAT | env_a_ctoh_v0210_gdr |	6 - 94 | 2002/05/14 to 2010/10/21 |	Reprocessing v2.1 (deprecated)| [nominal ERS orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_EN_Tracks_GE_OldOrbit.kmz) |
| ENVISAT | env_a_esa_v0300_sgdr |	6 - 94 | 2002/05/14 to 2010/10/21 |	Reprocessing ESA v3.0 | [nominal ERS orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_EN_Tracks_GE_OldOrbit.kmz) |
| Jason-1 | ja1_a_cnes_e_gdr |	1 - 259 | 2002/01/15 to 2009/01/26 |	GDR-E | [nominal Jason orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_RefOrbit_J3J2J1TP_Tracks_GoogleEarth_V3.kmz)|
| Jason-2 | ja2_a_cnes_d_sgdr |	0 - 303 | 2008/07/04 to 2016/10/02 |	GDR-D | [nominal Jason orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_RefOrbit_J3J2J1TP_Tracks_GoogleEarth_V3.kmz)|
| SARAL | srl_a_cnes_f_sgdr | 1 - 35 | 2013/03/14 to 2016/07/04 |	GDR-F | [nominal ERS orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_EN_Tracks_GE_OldOrbit.kmz) |
| CryoSat-2 | cs2_b_gop_c_gdr | 1 - 10 | 2010/10/01 to 2021/12/31 | Baseline C | [annual orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_C2_Tracks_HiRes.kmz), CryoSat orbit is drifting |
| CryoSat-2 | cs2_b_ice_d_gdr | 1 - 10 | 2010/10/01 to 2021/12/31 | Baseline D | [annual orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_C2_Tracks_HiRes.kmz), CryoSat orbit is dirfting |
| Jason-3 |	ja3_a_cnes_f_sgdr | 0 - | 2016/02/12 to now | GDR-F | [nominal Jason orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_RefOrbit_J3J2J1TP_Tracks_GoogleEarth_V3.kmz)|
| Sentinel-3A | s3a_a_lan_%_sgdr | 5 -  | 2016/06/15 to now | LAND IPF-06.10, IPF-06.14 | [nominal sentinel-3A orbit](https://sentinel.esa.int/documents/247904/685098/Sentinel-3-Relative-Ground-Tracks) |
| Sentinel-3B | s3b_b_lan_%_sgdr |	20 - | 2018/08/15 to now | LAND IPF-06.10, IPF-06.14 | [nominal sentinel-3B orbit](https://sentinel.esa.int/documents/247904/685098/Sentinel-3-Relative-Ground-Tracks) |
| Sentinel-6A LRM | s6a_a_lrm_%_gdr | 19 -  | 2021/05/21 to now | Baseline F04 | [nominal Jason orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_RefOrbit_J3J2J1TP_Tracks_GoogleEarth_V3.kmz)|
| Sentinel-6A SAR |	s6a_a_sar_%_gdr | 36 - | 2021/05/21 to now | Baseline F04 | [nominal Jason orbit](https://www.aviso.altimetry.fr/fileadmin/documents/data/tools/Visu_RefOrbit_J3J2J1TP_Tracks_GoogleEarth_V3.kmz)|                   



The products are updated for ongoing altimetry missions.


## Reference
- Frappart, Frédéric, Fabien Blarel, Ibrahim Fayad, Muriel Bergé-Nguyen, Jean-François Crétaux, Song Shu, Joël Schregenberger, and Nicolas Baghdadi. 2021. "Evaluation of the Performances of Radar and Lidar Altimetry Missions for Water Level Retrievals in Mountainous Environment: The Case of the Swiss Lakes" Remote Sensing 13, no. 11: 2196. https://doi.org/10.3390/rs13112196 

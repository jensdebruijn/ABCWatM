# -------------------------------------------------------------------------
# Name:        Soil module
# Purpose:
#
# Author:      PB
#
# Created:     15/07/2016
# Copyright:   (c) PB 2016 based on PCRGLOBE, LISFLOOD, HBV
# -------------------------------------------------------------------------

import numpy as np
from cwatm.management_modules.data_handling import cbinding, loadmap, divideValues, checkOption

class soil(object):

    """
    **SOIL**


    Calculation vertical transfer of water based on Arno scheme


    **Global variables**

    ====================  ================================================================================  =========
    Variable [self.var]   Description                                                                       Unit     
    ====================  ================================================================================  =========
    modflow               Flag: True if modflow_coupling = True in settings file                            --       
    storGroundwater       simulated groundwater storage                                                     m        
    capRiseFrac           fraction of a grid cell where capillar rise may happen                            m        
    cropKC                crop coefficient for each of the 4 different land cover types (forest, irrigated  --       
    EWRef                 potential evaporation rate from water surface                                     m        
    capillar              Simulated flow from groundwater to the third CWATM soil layer                     m        
    availWaterInfiltrati  quantity of water reaching the soil after interception, more snowmelt             m        
    potTranspiration      Potential transpiration (after removing of evaporation)                           m        
    actualET              simulated evapotranspiration from soil, flooded area and vegetation               m        
    soilLayers            Number of soil layers                                                             --       
    fracVegCover          Fraction of area covered by the corresponding landcover type                               
    rootDepth                                                                                                        
    soildepth             Thickness of the first soil layer                                                 m        
    soildepth12           Total thickness of layer 2 and 3                                                  m        
    KSat1                                                                                                            
    KSat2                                                                                                            
    KSat3                                                                                                            
    genuM1                                                                                                           
    genuM2                                                                                                           
    genuM3                                                                                                           
    genuInvM1                                                                                                        
    genuInvM2                                                                                                        
    genuInvM3                                                                                                        
    ws1                   Maximum storage capacity in layer 1                                               m        
    ws2                   Maximum storage capacity in layer 2                                               m        
    ws3                   Maximum storage capacity in layer 3                                               m        
    wres1                 Residual storage capacity in layer 1                                              m        
    wres2                 Residual storage capacity in layer 2                                              m        
    wres3                 Residual storage capacity in layer 3                                              m        
    wrange1                                                                                                          
    wrange2                                                                                                          
    wrange3                                                                                                          
    wfc1                  Soil moisture at field capacity in layer 1                                                 
    wfc2                  Soil moisture at field capacity in layer 2                                                 
    wfc3                  Soil moisture at field capacity in layer 3                                                 
    wwp1                  Soil moisture at wilting point in layer 1                                                  
    wwp2                  Soil moisture at wilting point in layer 2                                                  
    wwp3                  Soil moisture at wilting point in layer 3                                                  
    kunSatFC12                                                                                                       
    kunSatFC23                                                                                                       
    w1                    Simulated water storage in the layer 1                                            m        
    w2                    Simulated water storage in the layer 2                                            m        
    w3                    Simulated water storage in the layer 3                                            m        
    topwater              quantity of water above the soil (flooding)                                       m        
    arnoBeta                                                                                                         
    adjRoot                                                                                                          
    maxtopwater           maximum heigth of topwater                                                        m        
    directRunoff          Simulated surface runoff                                                          m        
    interflow             Simulated flow reaching runoff instead of groundwater                             m        
    openWaterEvap         Simulated evaporation from open areas                                             m        
    actTransTotal         Total actual transpiration from the three soil layers                             m        
    actBareSoilEvap       Simulated evaporation from the first soil layer                                   m        
    FrostIndexThreshold   Degree Days Frost Threshold (stops infiltration, percolation and capillary rise)  --       
    FrostIndex            FrostIndex - Molnau and Bissel (1983), A Continuous Frozen Ground Index for Floo  --       
    percolationImp        Fraction of area covered by the corresponding landcover type                      m        
    cropGroupNumber       soil water depletion fraction, Van Diepen et al., 1988: WOFOST 6.0, p.86, Dooren  --       
    cPrefFlow             Factor influencing preferential flow (flow from surface to GW)                    --       
    act_irrConsumption    actual irrgation water consumption                                                m        
    potBareSoilEvap       potential bare soil evaporation (calculated with minus snow evaporation)          m        
    totalPotET            Potential evaporation per land use class                                          m        
    rws                   Transpiration reduction factor (in case of water stress)                          --       
    prefFlow              Flow going directly from rainfall to groundwater                                  m        
    infiltration          Water actually infiltrating the soil                                              m        
    capRiseFromGW         Simulated capillary rise from groundwater                                         m        
    NoSubSteps            Number of sub steps to calculate soil percolation                                 --       
    perc1to2              Simulated water flow from soil layer 1 to soil layer 2                            m        
    perc2to3              Simulated water flow from soil layer 2 to soil layer 3                            m        
    perc3toGW             Simulated water flow from soil layer 3 to groundwater                             m        
    theta1                fraction of water in soil compartment 1 for each land use class                   --       
    theta2                fraction of water in soil compartment 2 for each land use class                   --       
    theta3                fraction of water in soil compartment 3 for each land use class                   --       
    actTransTotal_forest                                                                                             
    actTransTotal_grassl                                                                                             
    actTransTotal_paddy                                                                                              
    actTransTotal_nonpad                                                                                             
    before                                                                                                           
    gwRecharge            groundwater recharge                                                              m        
    ====================  ================================================================================  =========

    **Functions**
    """

    def __init__(self, model):
        self.var = model.data.HRU
        self.model = model

    def initial(self):
        """
        Initial part of the soil module

        * Initialize all the hydraulic properties of soil
        * Set soil depth

        """
        
        # self.var.permeability = float(cbinding('permeability'))

        self.var.soilLayers = 3
        # --- Topography -----------------------------------------------------

        # Fraction of area where percolation to groundwater is impeded [dimensionless]
        self.var.percolationImp = self.model.data.to_HRU(data=np.maximum(0,np.minimum(1,loadmap('percolationImp') * loadmap('factor_interflow'))), fn=None)  # checked

        # ------------ Preferential Flow constant ------------------------------------------
        self.var.cropGroupNumber = loadmap('cropgroupnumber')
        self.var.cropGroupNumber = self.model.data.to_HRU(data=self.var.cropGroupNumber, fn=None)  # checked
        # soil water depletion fraction, Van Diepen et al., 1988: WOFOST 6.0, p.86, Doorenbos et. al 1978
        # crop groups for formular in van Diepen et al, 1988

        # ------------ Preferential Flow constant ------------------------------------------
        self.var.cPrefFlow = self.model.data.to_HRU(data=loadmap('preferentialFlowConstant'), fn=None)

        # ------------ SOIL DEPTH ----------------------------------------------------------
        # soil thickness and storage

        soildepth = np.tile(self.var.full_compressed(np.nan, dtype=np.float32), (3, 1))

        # first soil layer = 5 cm
        soildepth[0] = self.var.full_compressed(0.05, dtype=np.float32)
        # second soil layer minimum 5cm
        stordepth1 = self.model.data.to_HRU(data=loadmap('StorDepth1'), fn=None)
        soildepth[1] = np.maximum(0.05, stordepth1 - soildepth[0])

        stordepth2 = self.model.data.to_HRU(data=loadmap('StorDepth2'), fn=None)
        soildepth[2] = np.maximum(0.05, stordepth2)

        # Calibration
        soildepth_factor =  loadmap('soildepth_factor')
        soildepth[1] = soildepth[1] * soildepth_factor
        soildepth[2] = soildepth[2] * soildepth_factor

        self.model.data.grid.soildepth_12 = self.model.data.to_grid(HRU_data=soildepth[1] + soildepth[2], fn='mean')
        return soildepth

    def dynamic(self, capillar, openWaterEvap, potTranspiration, potBareSoilEvap, totalPotET):
        """
        Dynamic part of the soil module

        For each of the land cover classes the vertical water transport is simulated
        Distribution of water holding capiacity in 3 soil layers based on saturation excess overland flow, preferential flow
        Dependend on soil depth, soil hydraulic parameters
        """

        from time import time
        t0 = time()

        if checkOption('calcWaterBalance'):
            w1_pre = self.var.w1.copy()
            w2_pre = self.var.w2.copy()
            w3_pre = self.var.w3.copy()
            topwater_pre = self.var.topwater.copy()

        bioarea = np.where(self.var.land_use_type < 4)[0].astype(np.int32)
        paddy_irrigated_land = np.where(self.var.land_use_type == 2)
        irrigated_land = np.where((self.var.land_use_type == 2) | (self.var.land_use_type == 3))
        availWaterInfiltration = self.var.natural_available_water_infiltration + self.var.actual_irrigation_consumption
        assert (availWaterInfiltration + 1e-6 >= 0).all()
        availWaterInfiltration[availWaterInfiltration < 0] = 0

        # depending on the crop calender -> here if cropKC > 0.75 paddies are flooded to 50mm (as set in settings file)

        self.var.topwater[paddy_irrigated_land] = np.where(self.var.cropKC[paddy_irrigated_land] > 0.75, self.var.topwater[paddy_irrigated_land] + availWaterInfiltration[paddy_irrigated_land], self.var.topwater[paddy_irrigated_land])

        # open water evaporation from the paddy field  - using potential evaporation from open water
        openWaterEvap[paddy_irrigated_land] = np.minimum(np.maximum(0., self.var.topwater[paddy_irrigated_land]), self.var.EWRef[paddy_irrigated_land])
        self.var.topwater[paddy_irrigated_land] = self.var.topwater[paddy_irrigated_land] - openWaterEvap[paddy_irrigated_land]

        assert (self.var.topwater >= 0).all()

        # if paddies are flooded, avail water is calculated before: top + avail, otherwise it is calculated here
        availWaterInfiltration[paddy_irrigated_land] = np.where(self.var.cropKC[paddy_irrigated_land] > 0.75, self.var.topwater[paddy_irrigated_land], self.var.topwater[paddy_irrigated_land] + availWaterInfiltration[paddy_irrigated_land])

        # open water can evaporate more than maximum bare soil + transpiration because it is calculated from open water pot evaporation
        potBareSoilEvap[paddy_irrigated_land] = np.maximum(0., potBareSoilEvap[paddy_irrigated_land] - openWaterEvap[paddy_irrigated_land])
        # if open water revaporation is bigger than bare soil, transpiration rate is reduced

        ### if GW capillary rise saturates soil layers, water is sent to the above layer, then to runoff
        self.var.w3[bioarea] = self.var.w3[bioarea] + capillar[bioarea]
        # CAPRISE from GW to soilayer 3 , if this is full it is send to soil layer 2
        self.var.w2[bioarea] = self.var.w2[bioarea] + np.where(self.var.w3[bioarea] > self.var.ws3[bioarea], self.var.w3[bioarea] - self.var.ws3[bioarea], 0)
        self.var.w3[bioarea] = np.minimum(self.var.ws3[bioarea], self.var.w3[bioarea])
        # CAPRISE from GW to soilayer 2 , if this is full it is send to soil layer 1
        self.var.w1[bioarea] = self.var.w1[bioarea] + np.where(self.var.w2[bioarea] > self.var.ws2[bioarea], self.var.w2[bioarea] - self.var.ws2[bioarea], 0)
        self.var.w2[bioarea] = np.minimum(self.var.ws2[bioarea], self.var.w2[bioarea])
        # CAPRISE from GW to soilayer 1 , if this is full it is send to saverunofffromGW
        saverunofffromGW = np.where(self.var.w1[bioarea] > self.var.ws1[bioarea], self.var.w1[bioarea] - self.var.ws1[bioarea], 0)
        self.var.w1[bioarea] = np.minimum(self.var.ws1[bioarea], self.var.w1[bioarea])

        assert (self.var.w1 >= 0).all()
        assert (self.var.w2 >= 0).all()
        assert (self.var.w3 >= 0).all()

        # ---------------------------------------------------------
        # calculate transpiration
        # ***** SOIL WATER STRESS ************************************

        etpotMax = np.minimum(0.1 * (totalPotET * 1000.), 1.0)
        # to avoid a strange behaviour of the p-formula's, ETRef is set to a maximum of 10 mm/day.

        p = self.var.full_compressed(np.nan, dtype=np.float32)

        # for irrigated land
        p[irrigated_land] = 1 / (0.76 + 1.5 * etpotMax[irrigated_land]) - 0.4
        # soil water depletion fraction (easily available soil water) # Van Diepen et al., 1988: WOFOST 6.0, p.87.
        p[irrigated_land] = p[irrigated_land] + (etpotMax[irrigated_land] - 0.6) / 4
        # correction for crop group 1  (Van Diepen et al, 1988) -> p between 0.14 - 0.77
        # The crop group number is a indicator of adaptation to dry climate,
        # e.g. olive groves are adapted to dry climate, therefore they can extract more water from drying out soil than e.g. rice.
        # The crop group number of olive groves is 4 and of rice fields is 1
        # for irrigation it is expected that the crop has a low adaptation to dry climate
 
        # for non-irrigated bioland
        non_irrigated_bioland = np.where((self.var.land_use_type == 0) | (self.var.land_use_type == 1))
        p[non_irrigated_bioland] = 1 / (0.76 + 1.5 * etpotMax[non_irrigated_bioland]) - 0.10 * (5 - self.var.cropGroupNumber[non_irrigated_bioland])
        # soil water depletion fraction (easily available soil water)
        # Van Diepen et al., 1988: WOFOST 6.0, p.87
        # to avoid a strange behaviour of the p-formula's, ETRef is set to a maximum of
        # 10 mm/day. Thus, p will range from 0.15 to 0.45 at ETRef eq 10 and
        # CropGroupNumber 1-5
        p[non_irrigated_bioland] = np.where(
            self.var.cropGroupNumber[non_irrigated_bioland] <= 2.5,
            p[non_irrigated_bioland] + (etpotMax[non_irrigated_bioland] - 0.6) / (self.var.cropGroupNumber[non_irrigated_bioland] * (self.var.cropGroupNumber[non_irrigated_bioland] + 3)),
            p[non_irrigated_bioland]
        )
        del non_irrigated_bioland
        del etpotMax
        # correction for crop groups 1 and 2 (Van Diepen et al, 1988)

        p = np.maximum(np.minimum(p, 1.0), 0.)[bioarea]
        # p is between 0 and 1 => if p =1 wcrit = wwp, if p= 0 wcrit = wfc
        # p is closer to 0 if evapo is bigger and cropgroup is smaller

        wCrit1 = ((1 - p) * (self.var.wfc1[bioarea] - self.var.wwp1[bioarea])) + self.var.wwp1[bioarea]
        wCrit2 = ((1 - p) * (self.var.wfc2[bioarea] - self.var.wwp2[bioarea])) + self.var.wwp2[bioarea]
        wCrit3 = ((1 - p) * (self.var.wfc3[bioarea] - self.var.wwp3[bioarea])) + self.var.wwp3[bioarea]

        del p

        # Transpiration reduction factor (in case of water stress)
        rws1 = divideValues((self.var.w1[bioarea] - self.var.wwp1[bioarea]), (wCrit1 - self.var.wwp1[bioarea]), default=1.)
        rws2 = divideValues((self.var.w2[bioarea] - self.var.wwp2[bioarea]), (wCrit2 - self.var.wwp2[bioarea]), default=1.)
        rws3 = divideValues((self.var.w3[bioarea] - self.var.wwp3[bioarea]), (wCrit3 - self.var.wwp3[bioarea]), default=1.)
        del wCrit1
        del wCrit2
        del wCrit3

        rws1 = np.maximum(np.minimum(1., rws1), 0.) * self.var.adjRoot[0][bioarea]
        rws2 = np.maximum(np.minimum(1., rws2), 0.) * self.var.adjRoot[1][bioarea]
        rws3 = np.maximum(np.minimum(1., rws3), 0.) * self.var.adjRoot[2][bioarea]

        TaMax = potTranspiration[bioarea] * (rws1 + rws2 + rws3)
        
        del potTranspiration
        del rws1
        del rws2
        del rws3

        # transpiration is 0 when soil is frozen
        TaMax = np.where(self.var.FrostIndex[bioarea] > self.var.FrostIndexThreshold, 0., TaMax)

        ta1 = np.maximum(np.minimum(TaMax * self.var.adjRoot[0][bioarea], self.var.w1[bioarea] - self.var.wwp1[bioarea]), 0.0)
        ta2 = np.maximum(np.minimum(TaMax * self.var.adjRoot[1][bioarea], self.var.w2[bioarea] - self.var.wwp2[bioarea]), 0.0)
        ta3 = np.maximum(np.minimum(TaMax * self.var.adjRoot[2][bioarea], self.var.w3[bioarea] - self.var.wwp3[bioarea]), 0.0)

        del TaMax

        self.var.w1[bioarea] = self.var.w1[bioarea] - ta1
        self.var.w2[bioarea] = self.var.w2[bioarea] - ta2
        self.var.w3[bioarea] = self.var.w3[bioarea] - ta3

        assert (self.var.w1 >= 0).all()
        assert (self.var.w2 >= 0).all()
        assert (self.var.w3 >= 0).all()

        self.var.actTransTotal[bioarea] = ta1 + ta2 + ta3

        del ta1
        del ta2
        del ta3

        # Actual potential bare soil evaporation - upper layer
        self.var.actBareSoilEvap[bioarea] = np.minimum(potBareSoilEvap[bioarea],np.maximum(0., self.var.w1[bioarea] - self.var.wres1[bioarea]))
        del potBareSoilEvap
        self.var.actBareSoilEvap[bioarea] = np.where(self.var.FrostIndex[bioarea] > self.var.FrostIndexThreshold, 0., self.var.actBareSoilEvap[bioarea])

        # no bare soil evaporation in the inundated paddy field
        self.var.actBareSoilEvap[paddy_irrigated_land] = np.where(self.var.topwater[paddy_irrigated_land] > 0., 0., self.var.actBareSoilEvap[paddy_irrigated_land])

        self.var.w1[bioarea] = self.var.w1[bioarea] - self.var.actBareSoilEvap[bioarea]

        # Infiltration capacity
        #  ========================================
        # first 2 soil layers to estimate distribution between runoff and infiltration
        soilWaterStorage =  self.var.w1[bioarea] + self.var.w2[bioarea]
        soilWaterStorageCap = self.var.ws1[bioarea] + self.var.ws2[bioarea]
        relSat = soilWaterStorage / soilWaterStorageCap
        relSat = np.minimum(relSat, 1.0)

        del soilWaterStorage

        satAreaFrac = 1 - (1 - relSat) ** self.var.arnoBeta[bioarea]
        # Fraction of pixel that is at saturation as a function of
        # the ratio Theta1/ThetaS1. Distribution function taken from
        # Zhao,1977, as cited in Todini, 1996 (JoH 175, 339-382)
        satAreaFrac = np.maximum(np.minimum(satAreaFrac, 1.0), 0.0)

        store = soilWaterStorageCap / (self.var.arnoBeta[bioarea] + 1)
        potBeta = (self.var.arnoBeta[bioarea] + 1) / self.var.arnoBeta[bioarea]
        potInf = store - store * (1 - (1 - satAreaFrac) ** potBeta)

        del satAreaFrac
        del potBeta
        del store
        del soilWaterStorageCap

        # ------------------------------------------------------------------
        # calculate preferential flow
        prefFlow = self.var.full_compressed(0, dtype=np.float32)
        prefFlow[bioarea] = availWaterInfiltration[bioarea] * relSat ** self.var.cPrefFlow
        prefFlow[bioarea] = np.where(self.var.FrostIndex[bioarea] > self.var.FrostIndexThreshold, 0.0, prefFlow[bioarea])
        prefFlow[paddy_irrigated_land] = 0

        del relSat

        prefFlow[bioarea] = prefFlow[bioarea] * (1 - self.var.capriseindex[bioarea])

        # ---------------------------------------------------------
        # calculate infiltration
        # infiltration, limited with KSat1 and available water in topWaterLayer
        infiltration = self.var.full_compressed(0, dtype=np.float32)
        infiltration[bioarea] = np.minimum(potInf, availWaterInfiltration[bioarea] - prefFlow[bioarea])
        del potInf
        infiltration[bioarea] = np.where(self.var.FrostIndex[bioarea] > self.var.FrostIndexThreshold, 0.0, infiltration[bioarea])
        
        directRunoff = self.var.full_compressed(0, dtype=np.float32)
        directRunoff[bioarea] = np.maximum(0., availWaterInfiltration[bioarea] - infiltration[bioarea] - prefFlow[bioarea])

        del availWaterInfiltration

        self.var.topwater[paddy_irrigated_land] = np.maximum(0.,  self.var.topwater[paddy_irrigated_land] - infiltration[paddy_irrigated_land])
        # if paddy fields flooded only runoff if topwater > 0.05m
        h = np.maximum(0., self.var.topwater[paddy_irrigated_land] - self.var.maxtopwater)
        directRunoff[paddy_irrigated_land] = np.where(self.var.cropKC[paddy_irrigated_land] > 0.75, h, directRunoff[paddy_irrigated_land])
        del h
        self.var.topwater[paddy_irrigated_land] = np.maximum(0., self.var.topwater[paddy_irrigated_land] - directRunoff[paddy_irrigated_land])

        directRunoff[bioarea] = directRunoff[bioarea] + saverunofffromGW
        # ADDING EXCESS WATER FROM GW CAPILLARY RISE

        del saverunofffromGW

        # infiltration to soilayer 1 , if this is full it is send to soil layer 2
        self.var.w1[bioarea] = self.var.w1[bioarea] + infiltration[bioarea]
        self.var.w2[bioarea] = self.var.w2[bioarea] + np.where(self.var.w1[bioarea] > self.var.ws1[bioarea], self.var.w1[bioarea] - self.var.ws1[bioarea], 0) #now w2 could be over-saturated
        self.var.w1[bioarea] = np.minimum(self.var.ws1[bioarea], self.var.w1[bioarea])

        del infiltration
        assert (self.var.w1 >= 0).all()
        assert (self.var.w2 >= 0).all()
        assert (self.var.w3 >= 0).all()

        # Available water in both soil layers [m]
        availWater1 = np.maximum(0., self.var.w1[bioarea] - self.var.wres1[bioarea])
        availWater2 = np.maximum(0., self.var.w2[bioarea] - self.var.wres2[bioarea])
        availWater3 = np.maximum(0., self.var.w3[bioarea] - self.var.wres3[bioarea])

        satTerm2 = availWater2 / (self.var.ws2[bioarea] - self.var.wres2[bioarea])
        satTerm3 = availWater3 / (self.var.ws3[bioarea] - self.var.wres3[bioarea])

        satTerm2[satTerm2 < 0] = 0
        satTerm2[satTerm2 > 1] = 1
        satTerm3[satTerm3 < 0] = 0
        satTerm3[satTerm3 > 1] = 1
        
        # Saturation term in Van Genuchten equation (always between 0 and 1)
        assert (satTerm2 >= 0).all() and (satTerm2 <= 1).all()
        assert (satTerm3 >= 0).all() and (satTerm3 <= 1).all()


        kUnSat2 = self.var.KSat2[bioarea] * np.sqrt(satTerm2) * np.square(1 - (1 - satTerm2 ** (1 / (self.var.lambda2[bioarea] / (self.var.lambda2[bioarea] + 1)))) ** (self.var.lambda2[bioarea] / (self.var.lambda2[bioarea] + 1)))
        kUnSat3 = self.var.KSat3[bioarea] * np.sqrt(satTerm3) * np.square(1 - (1 - satTerm3 ** (1 / (self.var.lambda3[bioarea] / (self.var.lambda3[bioarea] + 1)))) ** (self.var.lambda3[bioarea] / (self.var.lambda3[bioarea] + 1)))

        ## ----------------------------------------------------------
        # Capillar Rise
        satTermFC1 = np.maximum(0., self.var.w1[bioarea] - self.var.wres1[bioarea]) / (self.var.wfc1[bioarea] - self.var.wres1[bioarea])
        satTermFC2 = np.maximum(0., self.var.w2[bioarea] - self.var.wres2[bioarea]) / (self.var.wfc2[bioarea] - self.var.wres2[bioarea])

        capRise1 = np.minimum(np.maximum(0., (1 - satTermFC1) * kUnSat2), self.var.kunSatFC12[bioarea]) 
        capRise2 = np.minimum(np.maximum(0., (1 - satTermFC2) * kUnSat3), self.var.kunSatFC23[bioarea])

        capRise2 = np.minimum(capRise2, availWater3)

        del satTermFC1
        del satTermFC2

        assert (self.var.w1 >= 0).all()
        assert (self.var.w2 >= 0).all()
        assert (self.var.w3 >= 0).all()

        self.var.w1[bioarea] = self.var.w1[bioarea] + capRise1
        self.var.w2[bioarea] = self.var.w2[bioarea] - capRise1 + capRise2
        self.var.w3[bioarea] = self.var.w3[bioarea] - capRise2

        assert (self.var.w1 >= 0).all()
        assert (self.var.w2 >= 0).all()
        assert (self.var.w3 >= 0).all()

        del capRise1
        del capRise2

        # Percolation -----------------------------------------------
        # Available water in both soil layers [m]
        availWater1 = np.maximum(0., self.var.w1[bioarea] - self.var.wres1[bioarea])
        availWater2 = np.maximum(0., self.var.w2[bioarea] - self.var.wres2[bioarea])
        availWater3 = np.maximum(0., self.var.w3[bioarea] - self.var.wres3[bioarea])

        # Available storage capacity in subsoil
        capLayer2 = self.var.ws2[bioarea] - self.var.w2[bioarea]
        capLayer3 = self.var.ws3[bioarea] - self.var.w3[bioarea]

        satTerm1 = availWater1 / (self.var.ws1[bioarea] - self.var.wres1[bioarea])
        satTerm2 = availWater2 / (self.var.ws2[bioarea] - self.var.wres2[bioarea])
        satTerm3 = availWater3 / (self.var.ws3[bioarea] - self.var.wres3[bioarea])

        # Saturation term in Van Genuchten equation (always between 0 and 1)
        satTerm1 = np.maximum(np.minimum(satTerm1, 1.0), 0)
        satTerm2 = np.maximum(np.minimum(satTerm2, 1.0), 0)
        satTerm3 = np.maximum(np.minimum(satTerm3, 1.0), 0)

        # Unsaturated conductivity
        kUnSat1 = self.var.KSat1[bioarea] * np.sqrt(satTerm1) * np.square(1 - (1 - satTerm1 ** (1 / (self.var.lambda1[bioarea] / (self.var.lambda1[bioarea] + 1)))) ** (self.var.lambda1[bioarea] / (self.var.lambda1[bioarea] + 1)))
        kUnSat2 = self.var.KSat2[bioarea] * np.sqrt(satTerm2) * np.square(1 - (1 - satTerm2 ** (1 / (self.var.lambda2[bioarea] / (self.var.lambda2[bioarea] + 1)))) ** (self.var.lambda2[bioarea] / (self.var.lambda2[bioarea] + 1)))
        kUnSat3 = self.var.KSat3[bioarea] * np.sqrt(satTerm3) * np.square(1 - (1 - satTerm3 ** (1 / (self.var.lambda3[bioarea] / (self.var.lambda3[bioarea] + 1)))) ** (self.var.lambda3[bioarea] / (self.var.lambda3[bioarea] + 1)))

        self.model.NoSubSteps = 3
        DtSub = 1. / self.model.NoSubSteps

        # Copy current value of W1 and W2 to temporary variables,
        # because computed fluxes may need correction for storage
        # capacity of subsoil and in case soil is frozen (after loop)
        wtemp1 = self.var.w1[bioarea].copy()
        wtemp2 = self.var.w2[bioarea].copy()
        wtemp3 = self.var.w3[bioarea].copy()

        # Initialize top- to subsoil flux (accumulated value for all sub-steps)
        # Initialize fluxes out of subsoil (accumulated value for all sub-steps)
        perc1to2 = self.var.zeros(bioarea.size, dtype=np.float32)
        perc2to3 = self.var.zeros(bioarea.size, dtype=np.float32)
        perc3toGW = self.var.full_compressed(0, dtype=np.float32)

        assert (self.var.w1 >= 0).all()
        assert (self.var.w2 >= 0).all()
        assert (self.var.w3 >= 0).all()

        # Start iterating

        for i in range(self.model.NoSubSteps):
            if i > 0:
                # Saturation term in Van Genuchten equation
                satTerm1 = np.maximum(0., wtemp1 - self.var.wres1[bioarea]) / (self.var.ws1[bioarea] - self.var.wres1[bioarea])
                satTerm2 = np.maximum(0., wtemp2 - self.var.wres2[bioarea]) / (self.var.ws2[bioarea] - self.var.wres2[bioarea])
                satTerm3 = np.maximum(0., wtemp3 - self.var.wres3[bioarea]) / (self.var.ws3[bioarea] - self.var.wres3[bioarea])

                satTerm1 = np.maximum(np.minimum(satTerm1, 1.0), 0)
                satTerm2 = np.maximum(np.minimum(satTerm2, 1.0), 0)
                satTerm3 = np.maximum(np.minimum(satTerm3, 1.0), 0)

                # Unsaturated hydraulic conductivities
                kUnSat1 = self.var.KSat1[bioarea] * np.sqrt(satTerm1) * np.square(1 - (1 - satTerm1 ** (1 / (self.var.lambda1[bioarea] / (self.var.lambda1[bioarea] + 1)))) ** (self.var.lambda1[bioarea] / (self.var.lambda1[bioarea] + 1)))
                kUnSat2 = self.var.KSat2[bioarea] * np.sqrt(satTerm2) * np.square(1 - (1 - satTerm2 ** (1 / (self.var.lambda2[bioarea] / (self.var.lambda2[bioarea] + 1)))) ** (self.var.lambda2[bioarea] / (self.var.lambda2[bioarea] + 1)))
                kUnSat3 = self.var.KSat3[bioarea] * np.sqrt(satTerm3) * np.square(1 - (1 - satTerm3 ** (1 / (self.var.lambda3[bioarea] / (self.var.lambda3[bioarea] + 1)))) ** (self.var.lambda3[bioarea] / (self.var.lambda3[bioarea] + 1)))

            # Flux from top- to subsoil
            subperc1to2 =  np.minimum(availWater1, np.minimum(kUnSat1 * DtSub, capLayer2))
            subperc2to3 =  np.minimum(availWater2, np.minimum(kUnSat2 * DtSub, capLayer3))
            subperc3toGW = np.minimum(availWater3, np.minimum(kUnSat3 * DtSub, availWater3)) * (1 - self.var.capriseindex[bioarea])

            # Update water balance for all layers
            availWater1 = availWater1 - subperc1to2
            availWater2 = availWater2 + subperc1to2 - subperc2to3
            availWater3 = availWater3 + subperc2to3 - subperc3toGW
            # Update WTemp1 and WTemp2

            wtemp1 = availWater1 + self.var.wres1[bioarea]
            wtemp2 = availWater2 + self.var.wres2[bioarea]
            wtemp3 = availWater3 + self.var.wres3[bioarea]

            # Update available storage capacity in layer 2,3
            capLayer2 = self.var.ws2[bioarea] - wtemp2
            capLayer3 = self.var.ws3[bioarea] - wtemp3

            perc1to2  += subperc1to2
            perc2to3  += subperc2to3
            perc3toGW[bioarea] += subperc3toGW

            assert not np.isnan(perc1to2).any()
            assert not np.isnan(perc2to3).any()
            assert not np.isnan(perc3toGW[bioarea]).any()

            del subperc1to2
            del subperc2to3
            del subperc3toGW

            del kUnSat1
            del kUnSat2
            del kUnSat3
        
        del satTerm1
        del satTerm2
        del satTerm3

        del capLayer2
        del capLayer3

        del wtemp1
        del wtemp2
        del wtemp3

        del availWater1
        del availWater2
        del availWater3

        # When the soil is frozen (frostindex larger than threshold), no perc1 and 2
        perc1to2 = np.where(self.var.FrostIndex[bioarea] > self.var.FrostIndexThreshold, 0, perc1to2)
        perc2to3 = np.where(self.var.FrostIndex[bioarea] > self.var.FrostIndexThreshold, 0, perc2to3)

        # Update soil moisture
        assert (self.var.w1 >= 0).all()
        self.var.w1[bioarea] = self.var.w1[bioarea] - perc1to2
        assert (self.var.w1 >= 0).all()
        self.var.w2[bioarea] = self.var.w2[bioarea] + perc1to2 - perc2to3
        assert (self.var.w2 >= 0).all()
        self.var.w3[bioarea] = self.var.w3[bioarea] + perc2to3 - perc3toGW[bioarea]
        assert (self.var.w3 >= 0).all()

        assert not np.isnan(self.var.w1).any()
        assert not np.isnan(self.var.w2).any()
        assert not np.isnan(self.var.w3).any()

        del perc1to2
        del perc2to3

        # self.var.theta1[bioarea] = self.var.w1[bioarea] / rootDepth1[bioarea]
        # self.var.theta2[bioarea] = self.var.w2[bioarea] / rootDepth2[bioarea]
        # self.var.theta3[bioarea] = self.var.w3[bioarea] / rootDepth3[bioarea]

        # ---------------------------------------------------------------------------------------------
        # Calculate interflow

        # total actual transpiration
        #self.var.actTransTotal[No] = actTrans[0] + actTrans[1] + actTrans[2]
        #self.var.actTransTotal[No] =  np.sum(actTrans, axis=0)
       
        #This relates to deficit conditions, and calculating the ratio of actual to potential transpiration

        # total actual evaporation + transpiration
        self.var.actualET[bioarea] = self.var.actualET[bioarea] + self.var.actBareSoilEvap[bioarea] + openWaterEvap[bioarea] + self.var.actTransTotal[bioarea]

        #  actual evapotranspiration can be bigger than pot, because openWater is taken from pot open water evaporation, therefore self.var.totalPotET[No] is adjusted
        # totalPotET[bioarea] = np.maximum(totalPotET[bioarea], self.var.actualET[bioarea])

        # net percolation between upperSoilStores (positive indicating downward direction)
        #elf.var.netPerc[No] = perc[0] - capRise[0]
        #self.var.netPercUpper[No] = perc[1] - capRise[1]

        # groundwater recharge
        toGWorInterflow = perc3toGW[bioarea] + prefFlow[bioarea]

        interflow = self.var.full_compressed(0, dtype=np.float32)
        interflow[bioarea] = self.var.percolationImp[bioarea] * toGWorInterflow

        groundwater_recharge = self.var.full_compressed(0, dtype=np.float32)
        groundwater_recharge[bioarea] = (1 - self.var.percolationImp[bioarea]) * toGWorInterflow

        assert not np.isnan(interflow).any()
        assert not np.isnan(groundwater_recharge).any()

        if checkOption('calcWaterBalance'):
            self.model.waterbalance_module.waterBalanceCheck(
                how='cellwise',
                influxes=[self.var.natural_available_water_infiltration[bioarea], capillar[bioarea], self.var.actual_irrigation_consumption[bioarea]],
                outfluxes=[directRunoff[bioarea], perc3toGW[bioarea], prefFlow[bioarea], self.var.actTransTotal[bioarea], self.var.actBareSoilEvap[bioarea], openWaterEvap[bioarea]],
                prestorages=[w1_pre[bioarea], w2_pre[bioarea], w3_pre[bioarea], topwater_pre[bioarea]],
                poststorages=[self.var.w1[bioarea], self.var.w2[bioarea], self.var.w3[bioarea], self.var.topwater[bioarea]],
                tollerance=1e-6
            )

            self.model.waterbalance_module.waterBalanceCheck(
                how='cellwise',
                influxes=[self.var.natural_available_water_infiltration[bioarea], capillar[bioarea], self.var.actual_irrigation_consumption[bioarea], self.var.snowEvap[bioarea], self.var.interceptEvap[bioarea]],
                outfluxes=[directRunoff[bioarea], interflow[bioarea], groundwater_recharge[bioarea], self.var.actualET[bioarea]],
                prestorages=[w1_pre[bioarea], w2_pre[bioarea], w3_pre[bioarea], topwater_pre[bioarea]],
                poststorages=[self.var.w1[bioarea], self.var.w2[bioarea], self.var.w3[bioarea], self.var.topwater[bioarea]],
                tollerance=1e-6
            )

        print(time() - t0)

        return interflow, directRunoff, groundwater_recharge, perc3toGW, prefFlow, openWaterEvap
#ifndef ANALYZER_H
#define ANALYZER_H

#ifndef LOGIC2
  #define LOGIC2
#endif

#include <Analyzer.h>
#include "ll_results.h"

enum updi_state
{
    SYNC
};

enum FrameFlags {
    FLAG_NONE,
    FLAG_IDLE, 
    FLAG_BREAK, 
    FLAG_SYNC, 
    FLAG_DATA, 
    FLAG_ACK, 
    FLAG_WRONG_BIT, 
    FLAG_WIDE,
    FLAG_NARROW,
    FLAG_START, 
    FLAG_RATE
};

class settings;
class ll_analyzer : public Analyzer2
{
  public:
    ll_analyzer();

    virtual ~ll_analyzer();
    virtual void SetupResults();
    virtual void WorkerThread();

    virtual U32 GenerateSimulationData( U64 newest_sample_requested, U32 sample_rate, SimulationChannelDescriptor** simulation_channels );
    virtual U32 GetMinimumSampleRateHz();

    virtual const char* GetAnalyzerName() const;
    virtual bool NeedsRerun();

    bool Valid( BitState bit, U64 width);
    U64 CurrentWidth();
    void Identify(U64 start, const char* note, FrameFlags flag = FLAG_NONE, int value = 0);

#pragma warning( push )
#pragma warning(                                                                                                                           \
    disable : 4251 ) // warning C4251: 'UPDIAnalyzer::<...>' : class <...> needs to have dll-interface to be used by clients of class

  protected: // functions
    void ComputeSampleOffsets();

  protected: // vars
    std::unique_ptr<ll_settings> mSettings;
    std::unique_ptr<ll_results> mResults;
    AnalyzerChannelData* channel;

    // Serial analysis vars:
    U32 mSampleRateHz;
    U64 RateWidth;
    U64 last_bit;

#pragma warning( pop )
};

extern "C" ANALYZER_EXPORT const char* __cdecl GetAnalyzerName();
extern "C" ANALYZER_EXPORT Analyzer* __cdecl CreateAnalyzer();
extern "C" ANALYZER_EXPORT void __cdecl DestroyAnalyzer( Analyzer* analyzer );

#endif // ANALYZER_H

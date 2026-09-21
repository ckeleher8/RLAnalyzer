using System.IO;
using System.Threading.Tasks;
using GatewayApi.Models;

namespace GatewayApi.Contracts
{
    public interface IMlModelClient
    {
        /// <summary>
        /// Sends a replay file stream to the Python ML engine and polls for the completed analysis report.
        /// </summary>
        Task<PythonAnalysisReport> AnalyzeReplayAsync(Stream fileStream, string fileName);
    }
}
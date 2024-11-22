using Microsoft.Extensions.DependencyInjection;

namespace CVDNCTestService
{

    [Scrutor.ServiceDescriptor(typeof(TestsStore), ServiceLifetime.Singleton)]
    public class TestsStore
    {
        public List<databrowseMsg.FileComment> fileComments = new List<databrowseMsg.FileComment> {
            new databrowseMsg.FileComment{ comment = "Hello", userGuid = "1" },
            new databrowseMsg.FileComment{ comment = "World", userGuid = "2" }
        };
    }
}
